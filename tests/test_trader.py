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

from qteasy import QT_CONFIG, DataSource, Operator, BaseStrategy
from qteasy.trade_recording import new_account, get_or_create_position, update_position
from qteasy.trader import Trader
from qteasy.broker import QuickBroker, Broker


class TestTrader(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        operator = Operator(strategies=['macd', 'dma'])
        broker = QuickBroker()
        config = {
            'market_open_time_am':  '09:30:00',
            'market_close_time_pm': '15:30:00',
            'market_open_time_pm':  '13:00:00',
            'market_close_time_am': '11:30:00',
            'exchange':             'SSE',
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
            'asset_pool':           'APPL, MSFT, GOOG, AMZN, FB, TSLA',
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
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_orders']:
            if test_ds.table_data_exists(table):
                test_ds.drop_table_data(table)
        # 创建一个ID=1的账户
        new_account('test_user1', 100000, test_ds)
        # 添加初始持仓
        get_or_create_position(account_id=1, symbol='APPL', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='MSFT', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='GOOG', position_type='short', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='AMZN', position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=100)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=100)
        update_position(position_id=3, data_source=test_ds, qty_change=200, available_qty_change=100)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)
        self.ts = Trader(1, operator, broker, config, test_ds, debug=True)

    def test_class(self):
        """Test class Trader"""
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        Thread(target=ts.run).start()
        time.sleep(1)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')
        time.sleep(1)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')  # should be ignored
        time.sleep(1)
        self.assertEqual(ts.status, 'sleeping')
        ts.add_task('wakeup')
        time.sleep(1)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(1)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')  # should be ignored
        time.sleep(1)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('resume')
        time.sleep(1)
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('stop')
        time.sleep(1)
        print(f'\ncurrent status: {ts.status}')

        print(f'test function run_task')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'running')
        ts.run_task('stop')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'running')
        ts.run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts.run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts.run_task('resume')
        self.assertEqual(ts.status, 'running')

    def test_class_properties(self):
        """Test function run_task"""
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'running')

        print('test properties account and account id')
        print(ts.account_id, ts.account)
        self.assertEqual(ts.account_id, 1)
        self.assertIsInstance(ts.account, dict)
        self.assertEqual(ts.account['user_name'], 'test_user1')
        self.assertEqual(ts.account['cash_amount'], 100000)
        self.assertEqual(ts.account['available_cash'], 100000)

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
        self.assertEqual(ts.asset_pool, ['APPL', 'MSFT', 'GOOG', 'AMZN', 'FB', 'TSLA'])

        print('test property account cash, positions and overview')
        print(f'cash: {ts.account_cash}\npositions: \n{ts.account_positions}')
        self.assertEqual(ts.account_cash, (100000, 100000))
        self.assertIsInstance(ts.account_positions, pd.DataFrame)
        self.assertTrue(np.allclose(ts.account_positions.loc['qty'], [200.0, 200.0, -200.0, 200.0, 0.0, 0.0]))
        self.assertTrue(np.allclose(ts.account_positions.loc['available_qty'], [100.0, 100.0, -100.0, 100.0, 0.0, 0.0]))
        print(f'overview: {ts.account_overview}')

        raise NotImplementedError

    def test_run_info_tasks(self):
        """ running tasks that retrieve trader and account information"""
        raise NotImplementedError

    def test_run_strategy(self):
        """ running task that runs strategy"""
        raise NotImplementedError

    def test_process_result(self):
        """ running task that processes result """
        raise NotImplementedError

    def test_run(self):
        """Test function run"""
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()

