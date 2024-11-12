import asyncio

from parse.parse_info import get_goods_info, get_info


# Main parse function
async def return_info():
    id_url = 'https://www.estatesales.net/api/sale-details?bypass=bycoordinatesanddistance:33.22633_-111.785174_250&include=saleshedule&select=id,orgName,orgWebsite,phoneNumbers,stateCode,cityName,postalCodeNumber,address,latitude,longitude,utcOffset,name,type,pictureCount,itemCount,auctionUrl,isPublished,orgPackageType,saleSchedule&explicitTypes=DateTime'
    good_info = await get_goods_info(id_url)
    id_list = [list(item.keys())[0] for item in good_info]
    some_info = await get_info(id_list)
    result = await merge_lists(good_info, some_info)
    return result

# Function of combining resources obtained from 2 queries
async def merge_dicts(dict1, dict2):
    merged = {}
    for key in dict1.keys() | dict2.keys():
        if key in dict1 and key in dict2:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                merged[key] = {**dict1[key], **dict2[key]}
            else:
                merged[key] = dict2[key]
        elif key in dict1:
            merged[key] = dict1[key]
        else:
            merged[key] = dict2[key]
    return merged


async def merge_lists(list1, list2):
    merged_list = []

    for d1, d2 in zip(list1, list2):
        key = list(d1.keys())[0]
        merged_dict = {key: await merge_dicts(d1[key], d2[key])}
        merged_list.append(merged_dict)

    return merged_list


if __name__ == '__main__':
    asyncio.run(return_info())
