import scrapy
import json
import pandas as pd
from datetime import datetime, timedelta
from dotmap import DotMap


class OrderReportSpider(scrapy.Spider):
    name = "order_report"

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If no dates provided, default to last 30 days
        self.from_date = from_date or (datetime.now() - timedelta(days=30)).strftime(
            "%Y-%m-%d"
        )
        self.to_date = to_date or datetime.now().strftime("%Y-%m-%d")
        self.secrets = self.load_secrets("secrets.json")

    @staticmethod
    def load_secrets(file_path):
        with open(file_path, "r") as file:
            return DotMap(json.load(file))

    def start_requests(self):

        yield scrapy.Request(
            self.secrets.login_url,
            callback=self.parse_login,
        )

    def parse_login(self, response):
        csrf_token = response.xpath("//input[@name='_token']/@value").get()
        if not csrf_token:
            self.logger.error("CSRF token not found!")
            return

        payload = {
            "email": self.secrets.email,
            "password": self.secrets.password,
            "_token": csrf_token,
        }

        yield scrapy.FormRequest(
            url=self.secrets.login_url,
            formdata=payload,
            callback=self.navigate_to_report_page,
        )

    def navigate_to_report_page(self, response):
        if "Dashboard" in response.text or response.url != self.secrets.login_url:
            self.logger.info("Login successful!")

            yield scrapy.Request(
                self.secrets.base_report_url,
                callback=self.set_date_range,
                dont_filter=True,
            )
        else:
            self.logger.error("Login failed! Check credentials or CSRF token.")

    def set_date_range(self, response):
        csrf_token = response.xpath("//input[@name='_token']/@value").get()
        if not csrf_token:
            self.logger.error("CSRF token for date range not found!")
            return

        payload = {"_token": csrf_token, "from": self.from_date, "to": self.to_date}

        yield scrapy.FormRequest(
            url=self.secrets.date_set_url,
            formdata=payload,
            callback=self.parse_report_pages,
            meta={"page": 1, "total_orders": []},
            dont_filter=True,
        )

    def parse_report_pages(self, response):
        if not response.xpath("//table[@id='columnSearchDatatable']"):
            self.logger.error("Failed to load report page. Retrying...")
            yield scrapy.Request(
                self.secrets.base_report_url,
                callback=self.set_date_range,
                dont_filter=True,
            )
            return

        rows = response.xpath("//table[@id='columnSearchDatatable']/tbody/tr")
        page = response.meta.get("page", 1)
        total_orders = response.meta.get("total_orders", [])

        if not rows:
            self.logger.info("No orders found for the selected date range.")
            self.save_data(total_orders)
            return

        for row in rows:
            try:
                order = {
                    "sl": row.xpath("./td[1]/text()").get("N/A").strip(),
                    "order_id": row.xpath("./td[2]/a/text()").get("N/A").strip(),
                    "order_start_date": row.xpath("./td[3]/text()").get("N/A").strip(),
                    "order_start_time": row.xpath("./td[4]/text()").get("N/A").strip(),
                    "order_end_date": row.xpath("./td[5]/text()").get("N/A").strip(),
                    "order_end_time": row.xpath("./td[6]/text()").get("N/A").strip(),
                    "sub_total": row.xpath("./td[7]/text()").get("N/A").strip(),
                    "shipping_cost": row.xpath("./td[8]/text()").get("N/A").strip(),
                    "discount_amount": row.xpath("./td[9]/th/text()|./td[9]/text()")
                    .get("N/A")
                    .strip(),
                    "grand_total": row.xpath("./td[10]/text()").get("N/A").strip(),
                    "order_status": row.xpath("./td[11]/text()").get("N/A").strip(),
                    "payment_status": row.xpath("./td[12]/text()").get("N/A").strip(),
                    "customer_name": row.xpath("./td[13]/a/span/text()")
                    .get("N/A")
                    .strip(),
                    "customer_mobile": row.xpath("./td[14]/text()").get("N/A").strip(),
                }

                order_url = row.xpath("./td[2]/a/@href").get()

                if order["order_id"] != "N/A" and order_url:
                    yield scrapy.Request(
                        response.urljoin(order_url),
                        callback=self.parse_order_details,
                        meta={"order": order, "total_orders": total_orders},
                    )
            except Exception as e:
                self.logger.error(f"Error parsing row: {e}")
                self.logger.error(f"Problematic row: {row.get()}")

        next_page = response.xpath("//a[contains(text(), 'Next')]/@href").get()

        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse_report_pages,
                meta={"page": page + 1, "total_orders": total_orders},
                dont_filter=True,
            )
        elif total_orders:
            self.save_data(total_orders)

    def parse_order_details(self, response):
        order = response.meta["order"]
        total_orders = response.meta["total_orders"]

        address_element = response.xpath(
            "//a[contains(@href, 'google.com/maps')]//p[@class='inv-street-addr']/text()"
        ).get()
        order["address"] = address_element.strip() if address_element else "N/A"

        total_orders.append(order)

        if len(total_orders) % 10 == 0:
            self.logger.info(f"Processed {len(total_orders)} orders")

        return None

    def closed(self, reason):
        if hasattr(self, "total_orders") and self.total_orders:
            self.save_data(self.total_orders)

    def save_data(self, orders):
        if not orders:
            self.logger.info("No orders to save.")
            return

        # Save as JSON
        with open("order_report.json", "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)

        # Save as Excel
        df = pd.DataFrame(orders)
        df.to_excel("order_report.xlsx", index=False)

        # Save as CSV
        df.to_csv("order_report.csv", index=False)

        self.logger.info(f"Total orders extracted: {len(orders)}")
        self.logger.info("Data saved in JSON, Excel, and CSV formats.")
