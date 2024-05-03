import { Connection, clusterApiUrl, PublicKey, LAMPORTS_PER_SOL } from "@solana/web3.js";
import { Metaplex } from "@metaplex-foundation/js";
import { CoinGeckoClient } from "coingecko-api-v3";
import { Telegraf, Markup } from "telegraf";
import { RAYDIUM_AUTHORITY, WRAPPED_SOL, TokenInfo, Config, truncateAddress, calculatePercentage, formatTokenSupply, checkValues, checkTokenPrice } from "./utils.js";

const solanaConnection = new Connection(clusterApiUrl('mainnet-beta'))
const bot = new Telegraf(Config.BOT_TOKEN);

const watchRayduim = () => {
  console.log("Websocket Running")
  solanaConnection.onLogs(
    RAYDIUM_AUTHORITY,
    ({ logs, err, signature }) => {
      if (logs && logs.some(log => log.includes("Program log: initialize2:"))) {
        console.log(signature)
        fetchOpenBookMarket(signature)
      }
    },
    'processed'
  )
};

const fetchOpenBookMarket = async (signature: string) => {
  const txn = await solanaConnection.getParsedTransaction(signature, { maxSupportedTransactionVersion: 0 })
  const data: any = txn?.meta?.postTokenBalances
  const tokenAIndex = 0
  const tokenBIndex = 1

  //get base token
  const tokenA = data[tokenAIndex]
  //fet quote token (Sol)
  const tokenB = data[tokenBIndex]

  //send data to TokenData
  const token = new TokenData(tokenA, tokenB)
  token.fetchBaseInfo()

}

class TokenData {
  private tokenA: TokenInfo;
  private tokenB: TokenInfo;
  public quoteToken: string;
  public baseToken: string;
  public quoteAmount: string;
  public baseAmount: string;
  private connection: Connection;
  public baseName: string;
  public baseSymbol: string;
  public baseInfo: string;
  public baseSupply: number | any;
  public mintAuthorityAddress: string;
  public freezeAuthorityAddress: string;
  public mutableMeta: string;
  private metaplex: Metaplex;
  private mint: PublicKey;
  private holdersInfo: string;
  public solPrice: number;
  private client: CoinGeckoClient;
  public quoteValue: number;
  public baseValue: number;
  constructor(tokenAObject: TokenInfo, tokenBObject: TokenInfo) {
    this.tokenA = tokenAObject
    this.tokenB = tokenBObject
    this.connection = new Connection(Config.RPC_CONNECTION)
    this.metaplex = Metaplex.make(this.connection)
    this.client = new CoinGeckoClient({
      timeout: 10000,
      autoRetry: true,
    });
  }

  async checkQuoteToken() {
    if (this.tokenA.mint === WRAPPED_SOL) {
      this.quoteToken = this.tokenA.mint
      this.quoteAmount = formatTokenSupply(this.tokenA.uiTokenAmount.uiAmount)
      // Our logic for working with single price 
      this.quoteValue = this.tokenA.uiTokenAmount.uiAmount
      this.baseToken = this.tokenB.mint
      this.baseAmount = formatTokenSupply(this.tokenB.uiTokenAmount.uiAmount)
      // Our logic for working with single price 
      this.baseValue = this.tokenB.uiTokenAmount.uiAmount
    } else {
      this.quoteToken = this.tokenB.mint
      this.quoteAmount = formatTokenSupply(this.tokenB.uiTokenAmount.uiAmount)
      // Our logic for working with single price 
      this.quoteValue = this.tokenB.uiTokenAmount.uiAmount
      this.baseToken = this.tokenA.mint
      this.baseAmount = formatTokenSupply(this.tokenA.uiTokenAmount.uiAmount)
      // Our logic for working with single price 
      this.baseValue = this.tokenA.uiTokenAmount.uiAmount
    }
    this.mint = new PublicKey(this.baseToken)
  }

  async fetchTokenSupply() {
    const supply = await this.connection.getTokenSupply(new PublicKey(this.baseToken), 'confirmed')
    this.baseSupply = supply.value.uiAmount
  }

  async fetchTopHolders() {
    let holdersInfo = "🐋 Holders\n"
    const topHolders = await this.connection.getTokenLargestAccounts(this.mint, 'finalized')
    topHolders.value.slice(0, 6).forEach(acct => {
      holdersInfo += `<a href="https://solscan.io/account/${acct.address.toBase58()}"> ${truncateAddress(acct.address.toString())} (${calculatePercentage(this.baseSupply, acct.uiAmount)}%)</a>\n`
    })
    this.holdersInfo = holdersInfo;
  }

  async priceQuote() {
    let price = await this.client.simplePrice({
      vs_currencies: 'usd',
      ids: 'solana'
    }
    )
    this.solPrice = price.solana.usd
  }

  async fetchBaseInfo() {
    const setInfo = await this.checkQuoteToken()
    const supply = await this.fetchTokenSupply()
    const holders = await this.fetchTopHolders()
    let price = await this.priceQuote()
    const token = await this.metaplex
      .nfts()
      .findByMint({ mintAddress: new PublicKey(this.baseToken) });

    this.baseName = token.name ? token.name : "";
    this.baseSymbol = token.symbol ? token.symbol : "";
    this.baseInfo = token.json?.description
      ? token.json?.description
      : "";
    this.mintAuthorityAddress = token.mint.mintAuthorityAddress !== null ? "No ⛔️" : "Yes ✅";
    this.freezeAuthorityAddress = token.mint.freezeAuthorityAddress !== null ? "No ⛔️" : "Yes ✅";
    this.mutableMeta = token.isMutable === true ? "Yes ⛔️" : "No ✅";

    //some logic perform
    const liquidtyValue = checkValues(this.quoteValue, this.solPrice)
    const _basePrice = checkTokenPrice(this.baseValue, this.quoteValue, this.solPrice)
    const mcap = (_basePrice * this.baseSupply).toLocaleString(undefined, { maximumFractionDigits: 2 })

    let basePrice = _basePrice.toLocaleString(undefined, { maximumFractionDigits: 8 })

    let msg = `${this.baseName} → (${this.baseSymbol})\n\nMeta™\nBase: ${this.baseAmount} ${this.baseName}\nQuote: ${this.quoteAmount} SOL → ($${liquidtyValue})\n\n`
    msg += `Token Mint → ${formatTokenSupply(this.baseSupply)} ${this.baseName}\nPrice ${this.baseName} → ($${basePrice})\nMarketCap → ($${mcap})\n\n${this.baseInfo}\n\n`
    msg += this.holdersInfo
    msg += `\n🔒 Risks\nMint Authority → ${this.mintAuthorityAddress}\nFreeze Authority → ${this.freezeAuthorityAddress}\nMutable Metadata → ${this.mutableMeta} `
    msg += `\n<a href="https://birdeye.so/token/${this.baseToken}?chain=solana">Birdeye</a> → <a href="http://raydium.io/swap/?inputCurrency=sol&outputCurrency=${this.baseToken}&fixed=in">Raydium</a> → <a href="https://dexscreener.com/solana/${this.baseToken}">Dexscreen</a> → <a href="https://rugcheck.xyz/tokens/${this.baseToken}">Rug Check</a>`
    const keyboard = [
      [
        Markup.button.url(
          "New Mint",
          "https://t.me/newlymint"
        )
      ],
    ];
    await bot.telegram.sendMessage(
      Config.CHANNEL_ID,
      msg,
      {
        parse_mode: 'HTML',
        reply_markup: {
          inline_keyboard: keyboard,
        },
      }
    )
  }
}


watchRayduim()