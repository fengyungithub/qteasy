# coding=utf-8
# ======================================
# File:     test_trader.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-09
# Desc:
#   Unittest for trader related functions
# ======================================

import unittest
import time
import sys

from threading import Thread

import pandas as pd
import numpy as np

import qteasy
from qteasy import QT_CONFIG, DataSource, Operator, BaseStrategy
from qteasy.trade_recording import new_account, get_or_create_position, update_position, save_parsed_trade_orders
from qteasy.trading_util import submit_order, process_trade_result, cancel_order
from qteasy.trader import Trader, TraderShell
from qteasy.broker import QuickBroker, Broker


class TestTrader(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        print('Setting up test Trader...')
        operator = Operator(strategies=['macd', 'dma'], op_type='step')
        operator.set_parameter(
                stg_id='dma',
                window_length=20,
                strategy_run_freq='H'
        )
        operator.set_parameter(
                stg_id='macd',
                window_length=30,
                strategy_run_freq='30min',
        )
        broker = QuickBroker()
        config = {
            'mode': 0,
            'market_open_time_am':  '09:30:00',
            'market_close_time_pm': '15:30:00',
            'market_open_time_pm':  '13:00:00',
            'market_close_time_am': '11:30:00',
            'exchange':             'SSE',
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
            'asset_pool':           '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
            'asset_type':           'E',
            'PT_buy_threshold':     0.05,
            'PT_sell_threshold':    0.05,
            'allow_sell_short':     False,
        }
        # 创建测试数据源
        data_test_dir = 'data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        test_ds = DataSource('file', file_type='hdf', file_loc=data_test_dir)
        test_ds = DataSource(
                'db',
                host=QT_CONFIG['test_db_host'],
                port=QT_CONFIG['test_db_port'],
                user=QT_CONFIG['test_db_user'],
                password=QT_CONFIG['test_db_password'],
                db_name=QT_CONFIG['test_db_name']
        )
        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if test_ds.table_data_exists(table):
                test_ds.drop_table_data(table)
        # 创建一个ID=1的账户
        new_account('test_user1', 100000, test_ds)
        # 添加初始持仓
        get_or_create_position(account_id=1, symbol='000001.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000002.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000004.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000005.SZ', position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)

        self.stoppage = 1.5
        # 添加测试交易订单以及交易结果
        print('Adding test trade orders and results...')
        parsed_signals_batch = (
            ['000001.SZ', '000002.SZ', '000004.SZ', '000006.SZ', '000007.SZ', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'sell', 'sell', 'buy', 'buy'],
            [100, 100, 300, 400, 500],
            [60.0, 70.0, 80.0, 90.0, 100.0],
        )
        # save first batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch[0],
                positions=parsed_signals_batch[1],
                directions=parsed_signals_batch[2],
                quantities=parsed_signals_batch[3],
                prices=parsed_signals_batch[4],
                data_source=test_ds,
        )
        # submit orders
        for order_id in order_ids:
            submit_order(order_id, test_ds)
        time.sleep(self.stoppage)
        parsed_signals_batch = (
            ['000001.SZ', '000004.SZ', '000005.SZ', '000007.SZ', ],
            ['long', 'long', 'long', 'long'],
            ['sell', 'buy', 'buy', 'sell'],
            [200, 200, 100, 300],
            [70.0, 30.0, 56.0, 79.0],
        )
        # save first batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch[0],
                positions=parsed_signals_batch[1],
                directions=parsed_signals_batch[2],
                quantities=parsed_signals_batch[3],
                prices=parsed_signals_batch[4],
                data_source=test_ds,
        )
        # submit orders
        for order_id in order_ids:
            submit_order(order_id, test_ds)

        # 添加交易订单执行结果
        delivery_config = {
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
        }
        raw_trade_result = {
            'order_id':        1,
            'filled_qty':      100,
            'price':           60.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        2,
            'filled_qty':      100,
            'price':           70.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      200,
            'price':           80.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        4,
            'filled_qty':      400,
            'price':           89.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        5,
            'filled_qty':      500,
            'price':           100.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      100,
            'price':           78.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        6,
            'filled_qty':      200,
            'price':           69.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        7,
            'filled_qty':      200,
            'price':           31.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        9,
            'filled_qty':      300,
            'price':           91.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        # order 8 is canceled
        cancel_order(8, test_ds, delivery_config)

        print('creating Trader object...')
        # 生成Trader对象
        self.ts = Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                config=config,
                datasource=test_ds,
                debug=False,
        )

    def test_trader_status(self):
        """Test class Trader"""
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        Thread(target=ts.run).start()
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('wakeup')  # should be ignored
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('resume')  # resume to previous status: sleeping
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('sleep')  # should be ignored
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('resume')  # resume to previous status: running
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('stop')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'stopped')
        print(f'\ncurrent status: {ts.status}')

        print(f'test function run_task, as running tasks off-line')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('stop')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts.run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts.run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts.run_task('resume')
        self.assertEqual(ts.status, 'running')
        ts.run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts.run_task('resume')
        self.assertEqual(ts.status, 'sleeping')

    def test_trader_properties(self):
        """Test function run_task"""
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'sleeping')

        print('test properties account and account id')
        print(ts.account_id, ts.account)
        self.assertEqual(ts.account_id, 1)
        self.assertIsInstance(ts.account, dict)
        self.assertEqual(ts.account['user_name'], 'test_user1')
        self.assertEqual(ts.account['cash_amount'], 73905.0)
        self.assertEqual(ts.account['available_cash'], 73905.0)

        print('test properties operator and broker')
        print(f'operator: {ts.operator}\nbroker: {ts.broker}')
        self.assertIsInstance(ts.operator, Operator)
        self.assertIsInstance(ts.operator[0], BaseStrategy)
        self.assertIsInstance(ts.operator[1], BaseStrategy)
        self.assertEqual(ts.operator[0].name, 'MACD')
        self.assertEqual(ts.operator[1].name, 'DMA')
        self.assertIsInstance(ts.broker, Broker)

        print('test property asset pool')
        print(f'asset pool: {ts.asset_pool}')
        self.assertIsInstance(ts.asset_pool, list)
        self.assertEqual(ts.asset_pool, ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])

        print('test property account cash, positions and overview')
        print(f'cash: {ts.account_cash}\npositions: \n{ts.account_positions}')
        self.assertEqual(ts.account_cash, (73905.0, 73905.0))
        self.assertIsInstance(ts.account_positions, pd.DataFrame)
        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        self.assertIsInstance(ts.non_zero_positions, pd.DataFrame)
        self.assertTrue(np.allclose(ts.non_zero_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.non_zero_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))

        print('test property history orders, cashes, and positions')
        print(f'history orders: \n{ts.history_orders}\n'
              f'history cashes: \n{ts.history_cashes}\n'
              f'history positions: \n{ts.history_positions}')
        ts.info()

    def test_trader_run(self):
        """Test full-fledged run with all tasks manually added"""
        ts = self.ts
        Thread(target=ts.run).start()  # start the trader
        time.sleep(self.stoppage)
        # 依次执行start, pre_open, open_market, run_stg - macd, run_stg - dma, close_market, post_close, stop
        ts.add_task('start')
        time.sleep(self.stoppage)
        print('added task start')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts.add_task('pre_open')
        time.sleep(self.stoppage)
        print('added task pre_open')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts.add_task('open_market')
        time.sleep(self.stoppage)
        print('added task open_market')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', {'strategy_ids': ['macd']})
        time.sleep(self.stoppage)
        print('added task run_strategy - macd')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', {'strategy_ids': ['dma']})
        time.sleep(self.stoppage)
        print('added task run_strategy - dma')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('sleep')
        time.sleep(self.stoppage)
        print('added task sleep')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'paused')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        print('added task wakeup')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', {'strategy_ids': ['macd', 'dma']})
        time.sleep(self.stoppage)
        print('added task run_strategy - macd, dma')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('close_market')
        time.sleep(self.stoppage)
        print('added task close_market')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'paused')
        ts.add_task('post_close')
        time.sleep(self.stoppage)
        print('added task post_close')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'stopped')
        ts.add_task('stop')
        time.sleep(self.stoppage)
        print('added task stop')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')

    def test_strategy_run(self):
        """Test strategy run"""
        ts = self.ts
        ts.run_task('start')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts.run_task('run_strategy', ['macd', 'dma'])
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts._stop()
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')

    def test_trader(self):
        """Test trader in a full-fledged simulation run"""
        # start the trader and broker in separate threads, set the trader to debug mode
        # and then manually generate task agenda and add task from agenda with twisted
        # current time, thus to test the trader in simulated real-time run.

        # 1, use trader._check_trade_day(sim_date) to simulate a trade day or non-trade day
        # 2, use trader._initialize_agenda(sim_time) to generate task agenda at a simulated time
        # 3, use trader._add_task_from_agenda(sim_time) to add task from agenda at a simulated time

        import datetime as dt

        ts = self.ts
        ts.debug = True
        Thread(target=ts.run).start()
        Thread(target=ts.broker.run).start()

        # generate task agenda in a non-trade day and empty list will be generated
        sim_date = dt.date(2019, 1, 1)  # a non-trade day
        sim_time = dt.time(0, 0, 0)  # midnight
        ts._check_trade_day(sim_date)
        ts._initialize_agenda(sim_time)
        ts._add_task_from_agenda(sim_time)

        print('\n========generated task agenda in a non-trade day========')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        print(f'trade day bool: {ts.is_trade_day}')
        print(f'task daily agenda: {ts.task_daily_agenda}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        self.assertEqual(ts.is_trade_day, False)
        self.assertEqual(ts.task_daily_agenda, [])

        # generate task agenda in a trade day and complete agenda will be generated depending on generate time
        sim_date = dt.date(2023, 5, 10)  # a trade day
        sim_time = dt.time(7, 0, 0)  # before morning market open
        ts._check_trade_day(sim_date)
        self.assertEqual(ts.is_trade_day, True)
        ts._initialize_agenda(sim_time)  # should generate complete agenda
        print('\n========generated task agenda before morning market open========')
        print(ts.task_daily_agenda)
        target_agenda = [
            ('09:25:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('09:31:00', 'run_strategy', ['macd']),
            ('10:00:00', 'run_strategy', ['macd', 'dma']),
            ('10:30:00', 'run_strategy', ['macd']),
            ('11:00:00', 'run_strategy', ['macd', 'dma']),
            ('11:30:00', 'run_strategy', ['macd']),
            ('11:35:00', 'sleep'),
            ('12:55:00', 'wakeup'),
            ('13:00:00', 'run_strategy', ['macd', 'dma']),
            ('13:30:00', 'run_strategy', ['macd']),
            ('14:00:00', 'run_strategy', ['macd', 'dma']),
            ('14:30:00', 'run_strategy', ['macd']),
            ('15:00:00', 'run_strategy', ['macd', 'dma']),
            ('15:29:00', 'run_strategy', ['macd']),
            ('15:30:00', 'close_market'),
            ('15:35:00', 'post_close'),
        ]
        self.assertEqual(ts.task_daily_agenda, target_agenda)
        # re_initialize_agenda at 10:35:27
        sim_time = dt.time(10, 35, 27)
        ts.task_daily_agenda = []
        ts._initialize_agenda(sim_time)
        print('\n========generated task agenda at 10:35:27========')
        print(ts.task_daily_agenda)
        target_agenda = [
            ('09:25:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('11:00:00', 'run_strategy', ['macd', 'dma']),
            ('11:30:00', 'run_strategy', ['macd']),
            ('11:35:00', 'sleep'),
            ('12:55:00', 'wakeup'),
            ('13:00:00', 'run_strategy', ['macd', 'dma']),
            ('13:30:00', 'run_strategy', ['macd']),
            ('14:00:00', 'run_strategy', ['macd', 'dma']),
            ('14:30:00', 'run_strategy', ['macd']),
            ('15:00:00', 'run_strategy', ['macd', 'dma']),
            ('15:29:00', 'run_strategy', ['macd']),
            ('15:30:00', 'close_market'),
            ('15:35:00', 'post_close'),
        ]
        self.assertEqual(ts.task_daily_agenda, target_agenda)

        # third, create a task agenda and execute tasks from the agenda at sim times
        sim_time = dt.time(10, 35, 27)
        print(f'\n==========start simulation run============')
        ts.task_daily_agenda = []
        ts._initialize_agenda(sim_time)
        # 为了简化测试流程，将除test_sim_times之外的task都删除,并确保每次执行一个task
        test_sim_times = [
            dt.time(9, 35, 0),  # should run task open_market
            dt.time(11, 00, 0),  # should run task run_strategy macd and dma
            dt.time(11, 35, 0),  # should run task sleep
            dt.time(12, 55, 0),  # should run task wakeup
            dt.time(15, 29, 0),  # should run task run_strategy macd
            dt.time(15, 30, 0),  # should run task close_market
            dt.time(15, 35, 0),  # should run task post_close
        ]
        ts.task_daily_agenda.pop(0)  # remove task pre_open
        ts.task_daily_agenda.pop(2)  # remove task run_strategy macd
        ts.task_daily_agenda.pop(4)  # remove task run_strategy macd dma
        ts.task_daily_agenda.pop(4)  # remove task run_strategy macd
        ts.task_daily_agenda.pop(4)  # remove task run_strategy macd dma
        ts.task_daily_agenda.pop(4)  # remove task run_strategy macd
        ts.task_daily_agenda.pop(4)  # remove task run_strategy macd dma
        print(f'task agenda after removing tasks: {ts.task_daily_agenda}')
        target_agenda = [
            ('09:30:00', 'open_market'),
            ('11:00:00', 'run_strategy', ['macd', 'dma']),
            ('11:35:00', 'sleep'),
            ('12:55:00', 'wakeup'),
            ('15:29:00', 'run_strategy', ['macd']),
            ('15:30:00', 'close_market'),
            ('15:35:00', 'post_close'),
        ]
        self.assertEqual(ts.task_daily_agenda, target_agenda)
        for sim_time in test_sim_times:
            ts._add_task_from_agenda(sim_time)
            # waite 1 second for orders to be generated
            time.sleep(1)
            print(f'=========simulating time: {sim_time}=========')
            print(f'trader status: {ts.status}')
            print(f'broker status: {ts.broker.status}')
            print(f'trade orders generated: {ts.history_orders}')
            # waite 5 seconds for order execution results to be generated
            time.sleep(5)
            print(f'trade orders executed: {ts.trade_results()}')

        # finally, stop the trader and broker
        print('\n==========stop trader and broker============')
        ts.run_task('stop')

        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')


if __name__ == '__main__':
    unittest.main()

