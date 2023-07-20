"""
lib.py is a library of functions and classes
"""
import psycopg2
import random
import os
from typing import Dict
import threading
import logging
import logging.handlers as handlers
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.engine import URL
from ib_insync import IB, Stock
from rich import console

my_console = console.Console()


def get_random_number():
    """
    Generates a random number between 9000 and 9999.
    """
    return random.randint(9000, 9999)


class StockData:
    """
    Stock is a class that represents a stock
    """

    def __init__(self, symbol: str, exchange: str, price: float):
        self.symbol = symbol
        self.exchange = exchange
        self.price = price


class StockDict:
    """
    StockDict is a thread safe dictionary of stocks
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.dict = {}  # type: Dict[str, Stock]

    def get(self, key: str) -> Stock:
        """
        Get a stock by key
        """
        with self.lock:
            return self.dict.get(key)

    def set(self, key: str, value: Stock):
        """
        Set a stock by key
        """
        with self.lock:
            self.dict[key] = value

    def remove(self, key: str):
        """
        Remove a stock by key
        """
        with self.lock:
            if key in self.dict:
                del self.dict[key]

    def get_stocks(self):
        """
        Get all stocks
        """
        with self.lock:
            return self.dict.values()


class Logger:
    """
    Logger is a logger that has a name
    """

    def __init__(self, name: str, verbose: bool = False) -> None:
        self.verbose = verbose
        self.name = name
        logger = logging.getLogger("my_app")
        logger.setLevel(logging.INFO)
        log_handler = handlers.RotatingFileHandler("app.log", maxBytes=500, backupCount=2)
        log_handler.setLevel(logging.INFO)
        logger.addHandler(log_handler)

    def debug(self, message: str):
        """
        Print an debug message
        """
        if self.verbose:
            self.info(message)

    def info(self, message: str):
        """
        Print an info message
        """
        my_console.print(f"[grey50]{self.name}->[/grey50]{message}")


class SubLogger:
    """
    SubLogger is a logger that has a sub name and color
    """

    def __init__(self, name: str, sub_name, sub_color: str, verbose: bool = False) -> None:
        self.verbose = verbose
        self.name = name
        self.sub_name = sub_name
        self.sub_color = sub_color

    def debug(self, message: str):
        """
        Print an debug message
        """
        if self.verbose:
            self.info(message)

    def info(self, message: str):
        """
        Print an info message
        """
        header = f"[orange_red1]{self.name}->[/orange_red1][{self.sub_color}]{self.sub_name}->[/{self.sub_color}]"
        my_console.print(f"{header}{message}")

    def error(self, message: str):
        """
        Print an error message
        """
        header = f"[orange_red1]{self.name}->[/orange_red1][{self.sub_color}]{self.sub_name}->[/{self.sub_color}]"
        my_console.print(f"{header}[red]{message}[/red]")


def surrounding_values(val, count, nums):
    """
    Return n values above and below val from nums.
    """

    # Sort the list in ascending order
    nums.sort()

    # Find the index of the first value greater than val
    index = 0
    while index < len(nums) and nums[index] <= val:
        index += 1

    # Initialize result lists for values above and below val
    above = []
    below = []

    # Collect n values above and below val
    for i in range(count):
        if index - i - 1 >= 0:
            below.insert(0, nums[index - i - 1])
        if index + i < len(nums):
            above.append(nums[index + i])

    # Combine and return the result
    return below + above


def get_nums(val, n, nums):
    """
    Return n values above and below val from nums.
    """
    # Find the index of the value in nums
    index = nums.index(val)

    # Determine the lower and upper indices
    lower_index = max(0, index - n)
    upper_index = min(len(nums) - 1, index + n)

    # Get the values from the list
    return nums[lower_index: upper_index + 1]


def get_engine() -> Engine:
    """
    Get a database engine
    """
    load_dotenv(override=True)
    host = os.environ.get("DB_HOST")
    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    database = os.environ.get("DB_NAME")

    db_url = URL.create(
        drivername="postgresql",
        username=username,
        host=host,
        database=database,
        password=password,
    )
    engine = create_engine(db_url)
    return engine


def get_ib(ib_client_id, log) -> IB:
    """
    Get an IB instance
    """
    ib = IB()
    ib_host = os.environ.get("IB_HOST")
    ib_port = os.environ.get("IB_PORT")
    log.debug(f"Connecting to IB host: {ib_host} port: {ib_port}")
    ib.connect(host=ib_host, port=ib_port, clientId=ib_client_id)
    return ib


def generate_connection_string():
    DB_HOST="rythm-db-server.c0ejlw7jmtwx.us-west-2.rds.amazonaws.com"
    DB_USER="postgres"
    DB_PASSWORD="password01234"
    DB_NAME="rythm_db"
    DB_PORT=5432
    connection_string = f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' password='{DB_PASSWORD}' port='{DB_PORT}'"
    return connection_string

def upsert_contract(
    symbol, 
    contract_id=None, 
    security_type=None, 
    expiry=None, 
    strike=None, 
    right=None, 
    multiplier=None, 
    exchange=None, 
    currency=None, 
    local_symbol=None, 
    trading_class=None, 
    primary_exchange=None, 
    include_expired=None, 
    security_id_type=None, 
    security_id=None, 
    enabled=None, 
    deleted_at=None, 
    expiration_date=None, 
    und_contract_id=None, 
    und_symbol=None
):
    try:
        conn = psycopg2.connect(generate_connection_string())
        cur = conn.cursor()

        # Check if symbol exists
        cur.execute("SELECT id FROM public.contract WHERE symbol = %s;", (symbol,))
        symbol_exists = cur.fetchone() is not None

        if symbol_exists:
            # Symbol exists, perform an update
            cur.execute("""
                UPDATE public.contract SET
                    contract_id = %s,
                    security_type = %s,
                    expiry = %s,
                    strike = %s,
                    "right" = %s,
                    multiplier = %s,
                    exchange = %s,
                    currency = %s,
                    local_symbol = %s,
                    trading_class = %s,
                    primary_exchange = %s,
                    include_expired = %s,
                    security_id_type = %s,
                    security_id = %s,
                    enabled = %s,
                    deleted_at = %s,
                    expiration_date = %s,
                    und_contract_id = %s,
                    und_symbol = %s
                WHERE symbol = %s;
            """, (
                contract_id,
                security_type,
                expiry,
                strike,
                right,
                multiplier,
                exchange,
                currency,
                local_symbol,
                trading_class,
                primary_exchange,
                include_expired,
                security_id_type,
                security_id,
                enabled,
                deleted_at,
                expiration_date,
                und_contract_id,
                und_symbol,
                symbol
            ))
        else:
            # Symbol does not exist, perform an insert
            cur.execute("""
                INSERT INTO public.contract (
                    contract_id, symbol, security_type, expiry, strike, "right", multiplier, 
                    exchange, currency, local_symbol, trading_class, primary_exchange, 
                    include_expired, security_id_type, security_id, enabled, deleted_at, 
                    expiration_date, und_contract_id, und_symbol
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                contract_id,
                symbol,
                security_type,
                expiry,
                strike,
                right,
                multiplier,
                exchange,
                currency,
                local_symbol,
                trading_class,
                primary_exchange,
                include_expired,
                security_id_type,
                security_id,
                enabled,
                deleted_at,
                expiration_date,
                und_contract_id,
                und_symbol
            ))

        # Commit the transaction
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
