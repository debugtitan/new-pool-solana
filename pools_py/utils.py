import struct
import base58 # type: ignore
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()
def format_number(n):
    amount = int(n)
    if amount < 1000:
        return str(amount)
    elif amount < 10**6:
        if amount % 1000 == 0:
            return f"{amount//1000}k"
        else:
            return f"{amount/1000:.{1}f}k"
    elif amount < 10**9:
        if amount % 10**6 == 0:
            return f"{amount//10**6}M"
        else:
            return f"{amount/10**6:.{1}f}M"
    elif amount < 10**12:
        if amount % 10**9 == 0:
            return f"{amount//10**9}B"
        else:
            return f"{amount/10**9:.{1}f}B"
    elif amount < 10**15:
        if amount % 10**12 == 0:
            return f"{amount//10**12}T"
        else:
            return f"{amount/10**12:.{1}f}T"
    elif amount < 10**18:
        if amount % 10**15 == 0:
            return f"{amount//10**15}Q"
        else:
            return f"{amount/10**15:.{1}f}Q"
    else:
        return str(amount)
    
def calculate_asset_value(amount):
    price_per_sol = cg.get_price('solana','usd')['solana']['usd']
    return amount * price_per_sol

def calculate_percentage(total_supply, user_holdings):
    percentage = (user_holdings / total_supply) * 100
    return "{:.2f}".format(percentage)

def truncate_address(address):
    if len(address) <= 14:
        return address
    else:
        prefix = address[:6]
        suffix = address[-6:]
        dots = '*' * 5
        return prefix + dots + suffix

#Recognition of code owners
#https://github.com/metaplex-foundation/python-api/blob/main/metaplex/metadata.py

async def unpack_metadata_account(data):
    assert(data[0] == 4)
    i = 1
    source_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    mint_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    name_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4
    name = struct.unpack('<' + "B"*name_len, data[i:i+name_len])
    i += name_len
    symbol_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    symbol = struct.unpack('<' + "B"*symbol_len, data[i:i+symbol_len])
    i += symbol_len
    uri_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    uri = struct.unpack('<' + "B"*uri_len, data[i:i+uri_len])
    i += uri_len
    fee = struct.unpack('<h', data[i:i+2])[0]
    i += 2
    has_creator = data[i] 
    i += 1
    creators = []
    verified = []
    share = []
    if has_creator:
        creator_len = struct.unpack('<I', data[i:i+4])[0]
        i += 4
        for _ in range(creator_len):
            creator = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
            creators.append(creator)
            i += 32
            verified.append(data[i])
            i += 1
            share.append(data[i])
            i += 1
    primary_sale_happened = bool(data[i])
    i += 1
    is_mutable = bool(data[i])
    metadata = {
        "update_authority": source_account,
        "mint": mint_account,
        "data": {
            "name": bytes(name).decode("utf-8").strip("\x00"),
            "symbol": bytes(symbol).decode("utf-8").strip("\x00"),
            "uri": bytes(uri).decode("utf-8").strip("\x00"),
            "seller_fee_basis_points": fee,
            "creators": creators,
            "verified": verified,
            "share": share,
        },
        "primary_sale_happened": primary_sale_happened,
        "is_mutable": is_mutable,
    }
    return metadata


