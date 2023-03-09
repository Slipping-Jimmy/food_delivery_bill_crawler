from datetime import date
from sys import argv
import re


def main(query):
    with open("fp_order.txt", encoding="utf-8") as fi:
        html = fi.read()

    y, m, d = query.split('-')
    print(y,m,d)
    date_query = date(int(y), int(m), int(d))

    ptn_res = '<h3 class="item-info item-title">([^<]+)</h3>'
    ptn_date = '<div class="item-info order-date">(\d+)年(\d+)月(\d+)日</div>'
    ptn_pri = '<div class="item-price">\$ ([^<]+)</div>'

    restaurants = [re.sub("\(.+\)|\s", '', res) for res in re.findall(ptn_res, html)]
    dates = [date(int(y), int(m), int(d)) for y, m, d in re.findall(ptn_date, html)]
    prices = [int(p.replace(" ", '')) for p in re.findall(ptn_pri, html)]

    tup = zip(restaurants, dates, prices)
    new_tup = filter(lambda t: t[1]> date_query  ,tup)

    for r, d, p in reversed(list(new_tup)):
        print(r,d,p, sep=',')


if __name__ == "__main__":
    # main(argv[1]) # 之前已記錄到 1999-9-9
    main('2022-09-25') # 之前已記錄到 1999-9-9