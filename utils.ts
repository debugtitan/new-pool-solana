import { PublicKey, clusterApiUrl } from "@solana/web3.js";
import 'dotenv/config.js'

export const RAYDIUM_AUTHORITY = new PublicKey("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")
export const WRAPPED_SOL = "So11111111111111111111111111111111111111112"

export const Config = {
    RPC_CONNECTION: process.env.RPC_CONNECTION || clusterApiUrl('mainnet-beta')
}

export function truncateAddress(address: string) {
    if (address.length <= 14) {
        return address;
    } else {
        let prefix = address.slice(0, 6);
        let suffix = address.slice(-6);
        let dots = '*'.repeat(5);
        return prefix + dots + suffix;
    }
}

export const calculatePercentage = (totalSupply: number, userHoldings: number | any) => {
    const percentage = (userHoldings / totalSupply) * 100;
    return percentage.toFixed(2)
}

export const formatTokenSupply = (tokenSupply: number) => {
    if (tokenSupply >= 1e15) {
        return (tokenSupply / 1e15).toFixed(2) + "Q";
    } else if (tokenSupply >= 1e12) {
        return (tokenSupply / 1e12).toFixed(2) + "T";
    } else if (tokenSupply >= 1e9) {
        return (tokenSupply / 1e9).toFixed(2) + "B";
    } else if (tokenSupply >= 1e6) {
        return (tokenSupply / 1e6).toFixed(2) + "M";
    } else if (tokenSupply >= 1000) {
        return (tokenSupply / 1000).toFixed(2) + "k";
    } else {
        return tokenSupply.toString();
    }
}

export const checkValues = (tokenAmount: number, price: number) => {
    return (tokenAmount * price).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

export const checkTokenPrice = (base: number, quote: number, price: number) => {
    return (quote / base) * price
}


type UiTokenAmount = {
    amount: string,
    decimals: number,
    uiAmount: number,
    uiAmountString: string
}

export type TokenInfo = {
    accountIndex: number,
    mint: string,
    owner: string,
    programId: string,
    uiTokenAmount: UiTokenAmount
}