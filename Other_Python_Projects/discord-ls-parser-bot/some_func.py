from config import redis_client
from parse.gathering_info import return_info


async def return_goods(user):
    info = await return_info()
    user_keywords = await redis_client.get(f"keywords:{user.id}")
    viewed_goods = await redis_client.smembers(f"viewed_goods:{user.id}")

    found_any = False

    if user_keywords:
        user_keywords = user_keywords.decode('utf-8').split(',')

    for i in info:
        good_id = list(i.keys())[0]

        if good_id in [v.decode('utf-8') for v in viewed_goods]:
            continue

        name = i[good_id]['name']
        desc = i[good_id]['desc']

        found_keywords = []
        if user_keywords:
            for keyword in user_keywords:
                if keyword.lower() in name.lower() or keyword.lower() in desc.lower():
                    found_keywords.append(keyword)

        if found_keywords and str(good_id) not in [v.decode('utf-8') for v in viewed_goods]:
            found_any = True

            await user.send(i[good_id]['main_picture']['url'])
            await user.send(
                f"Name: {name if len(name) < 100 else (name[:100] + '...')}\n"
                f"Type of sales: {i[good_id]['type_name']}\n"
                f"City_name: {i[good_id]['postal_code_number']} {i[good_id]['state_code']} {i[good_id]['city_name']}\n"
                f"Address: {i[good_id]['address'] if i[good_id]['address'] else 'Absent'}\n"
                f"Dates: {', and '.join(['from ' + await convert_time(date['localStartDate']['_value'][:9] + ' at ' + date['localStartDate']['_value'][11:-1]) + ' to ' + await convert_time(date['localEndDate']['_value'][:9] + ' at ' + date['localEndDate']['_value'][11:-1]) for date in i[good_id]['dates']])}\n"
                f"Url: https://www.estatesales.net/AZ/San-Tan-Valley/85140/{good_id}")
            await user.send(
                f"Description: {desc if len(desc) < 890 else desc[:885] + '...'}\n"
                f"Found keywords: {', '.join(found_keywords)}"
            )

            await redis_client.sadd(f"viewed_goods:{user.id}", good_id)

    return found_any


async def convert_time(date: str) -> str:
    date_part, time_part = date.split(' at ')

    hour, minute, second = map(int, time_part.split(':'))
    am_pm = "am" if hour < 12 else "pm"
    hour = hour % 12
    hour = hour if hour != 0 else 12

    formatted_time = f"{date_part} at {hour}{am_pm}"
    return formatted_time
