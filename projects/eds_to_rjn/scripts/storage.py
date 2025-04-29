import csv
def store_live_values(data, path):
    with open(path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if f.tell() == 0:  # file is empty
            writer.writeheader()
        writer.writerows(data)
    print("Live values stored.")