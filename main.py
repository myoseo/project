import csv

INITIAL_CASH = 1_000_000
SHORT_WINDOW = 5
LONG_WINDOW = 20
CSV_PATH = "data.csv"


def load_data(path):
    """CSV 파일에서 날짜와 종가 데이터를 읽어 날짜순으로 정렬합니다."""
    rows = []

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {"date", "close"}
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"CSV에 필수 컬럼이 없습니다: {', '.join(sorted(missing_columns))}")

        for row in reader:
            rows.append(
                {
                    "date": row["date"],
                    "close": int(row["close"]),
                }
            )

    rows.sort(key=lambda item: item["date"])
    return rows


def moving_average(data, index, window):
    """지정한 위치에서 window 기간의 단순 이동평균을 직접 계산합니다."""
    if index + 1 < window:
        return None

    total = 0
    for i in range(index - window + 1, index + 1):
        total += data[i]["close"]

    return total / window


def add_moving_averages(data):
    """각 행에 5일 이동평균선과 20일 이동평균선을 추가합니다."""
    for i in range(len(data)):
        data[i]["ma5"] = moving_average(data, i, SHORT_WINDOW)
        data[i]["ma20"] = moving_average(data, i, LONG_WINDOW)

    return data


def run_backtest(data):
    """5일/20일 이동평균선 교차 전략으로 CSV 기반 백테스트를 실행합니다."""
    if not data:
        raise ValueError("백테스트할 데이터가 없습니다.")

    cash = INITIAL_CASH
    stock = 0
    buy_price = 0
    trades = []

    for i in range(1, len(data)):
        yesterday = data[i - 1]
        today = data[i]

        if yesterday["ma5"] is None or yesterday["ma20"] is None:
            continue
        if today["ma5"] is None or today["ma20"] is None:
            continue

        prev_ma5 = yesterday["ma5"]
        prev_ma20 = yesterday["ma20"]
        now_ma5 = today["ma5"]
        now_ma20 = today["ma20"]
        price = today["close"]

        golden_cross = prev_ma5 <= prev_ma20 and now_ma5 > now_ma20
        dead_cross = prev_ma5 >= prev_ma20 and now_ma5 < now_ma20

        if stock == 0 and golden_cross:
            quantity = cash // price

            if quantity > 0:
                stock = quantity
                cash -= stock * price
                buy_price = price
                trades.append(
                    {
                        "date": today["date"],
                        "type": "BUY",
                        "price": price,
                        "quantity": stock,
                        "cash": cash,
                    }
                )
        elif stock > 0 and dead_cross:
            cash += stock * price
            profit_rate = ((price - buy_price) / buy_price) * 100
            trades.append(
                {
                    "date": today["date"],
                    "type": "SELL",
                    "price": price,
                    "quantity": stock,
                    "profit_rate": profit_rate,
                    "cash": cash,
                }
            )
            stock = 0
            buy_price = 0

    final_price = data[-1]["close"]
    final_value = cash + stock * final_price
    total_return = ((final_value - INITIAL_CASH) / INITIAL_CASH) * 100

    return final_value, total_return, trades, cash, stock


def print_result(final_value, total_return, trades, cash, stock):
    """백테스트 결과를 콘솔에 출력합니다."""
    print("===== 백테스트 결과 =====")
    print(f"초기 자금: {INITIAL_CASH:,}원")
    print(f"최종 평가금액: {final_value:,.0f}원")
    print(f"총 수익률: {total_return:.2f}%")
    print(f"거래 횟수: {len(trades)}회")
    print(f"남은 현금: {cash:,.0f}원")
    print(f"보유 주식 수: {stock}주")

    print()
    print("===== 거래 내역 =====")

    if not trades:
        print("거래 없음")
        return

    for trade in trades:
        if trade["type"] == "BUY":
            print(
                f'{trade["date"]} BUY '
                f'가격: {trade["price"]:,}원 '
                f'수량: {trade["quantity"]}주 '
                f'남은 현금: {trade["cash"]:,.0f}원'
            )
        else:
            print(
                f'{trade["date"]} SELL '
                f'가격: {trade["price"]:,}원 '
                f'수량: {trade["quantity"]}주 '
                f'수익률: {trade["profit_rate"]:.2f}% '
                f'현금: {trade["cash"]:,.0f}원'
            )


def main():
    data = load_data(CSV_PATH)
    data = add_moving_averages(data)
    final_value, total_return, trades, cash, stock = run_backtest(data)
    print_result(final_value, total_return, trades, cash, stock)


if __name__ == "__main__":
    main()
