def init():
    while True:
        temp = input("Please input station name: ")
        if temp:
            station_name = temp
            break
        else:
            print("Nothing input")
    while True:
        temp = input("Please input your key: ")
        if temp:
            station_key = temp
            break
        else:
            print("Nothing input")
    while True:
        temp = input("Please input endpoint(server): ")
        if temp:
            url = temp
            break
        else:
            print("Nothing input")
    while True:
        temp = input("Reflesh frequency: ")
        try:
            record_frequency = int(temp)
            break
        except ValueError as e:
            _ = e
            print("Error format\n")
    while True:
        temp = input("Log size: ")
        try:
            storage_size = int(temp)
            break
        except ValueError as e:
            _ = e
            print("Error format\n")
    t = [
        f"station_name = '{station_name}'\n",
        f"station_key = '{station_key}'\n",
        f"server = '{url}'\n",
        f"record_frequency = {record_frequency}\n",
        f"storage_size = {storage_size}\n",
    ]
    with open(".env.toml", "w") as f:
        f.writelines(t)
