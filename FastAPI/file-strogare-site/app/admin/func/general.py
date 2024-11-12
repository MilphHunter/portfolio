async def get_time(data):
    result = []
    for i in data:
        minute = i.created_at.minute if i.created_at.minute > 9 else f'0{i.created_at.minute}'
        hour = i.created_at.hour if i.created_at.hour > 9 else f'0{i.created_at.hour}'
        day = i.created_at.day if i.created_at.day > 9 else f'0{i.created_at.day}'
        month = i.created_at.month if i.created_at.month > 9 else f'0{i.created_at.month}'
        year = i.created_at.year if i.created_at.year > 9 else f'0{i.created_at.year}'
        result.append(f"{day}-{month}-{year} at {hour}:{minute}")
    return result
