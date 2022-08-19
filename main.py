import asyncio
import time
import meraki.aio
import pandas as pd
import datetime
from itertools import chain
import matplotlib.pyplot as plt

api_key = 'YOUR_API_KEY'
org_id = 'YOUR_ORG_ID'
sensor_serial = 'YOUR_SENSOR_SERIAL'
metric = 'temperature'
numdays = 365

aiomeraki = meraki.aio.AsyncDashboardAPI(api_key=api_key)

base = datetime.datetime.today()
date_list = [base - datetime.timedelta(days=x) for x in range(numdays)]

async def get_readings(t0, t1, aiomeraki):
    try:
        readings = await aiomeraki.sensor.getOrganizationSensorReadingsHistory(
            organizationId=org_id,
            total_pages=-1,
            metrics=[metric],
            serials=[sensor_serial],
            t0=t0.isoformat(),
            t1=t1.isoformat()
        )
    except meraki.AsyncAPIError as e:
        print(e)
        print(t0.isoformat())
        print(t1.isoformat())
        readings=[]
    return readings

async def main(aiomeraki, date_list):
    get_tasks = []
    for i in reversed(range(0, len(date_list), 7)):
        if i <= 0:
            pass
        elif i - 7 < 0:
            pass
        else:
            print("start", date_list[i])
            print("end", date_list[i - 7])
            get_tasks.append(get_readings(date_list[i], date_list[i-7], aiomeraki))

    results = []
    for task in asyncio.as_completed(get_tasks):
        result = await task
        results.append(result)
        time.sleep(0.1)

    return results

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(main(aiomeraki, date_list))

    print(len(results))

    df = pd.DataFrame(list(chain.from_iterable(results)))

    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    #pd.set_option('display.max_colwidth', -1)

    df = pd.concat([df.drop(["temperature"], axis=1), df["temperature"].apply(pd.Series)], axis=1)
    df = df.drop(["metric"], axis=1)
    df = df.set_index(["ts"])

    df.index = pd.to_datetime(df.index)
    df.index = df.index + pd.Timedelta('-5:00:00')
    df.index = df.index.tz_convert('Etc/GMT-5')
    df = df.sort_index(ascending=True)

    print(df)

    df.plot(figsize=[10, 7])
    plt.ylabel("degrees")
    plt.title("Temperature Data", fontsize=16)
    plt.legend(fontsize=14);
    plt.show()