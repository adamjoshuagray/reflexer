import numpy as np
import pandas as pd

import models.options as options
from models.constants import SPY, RAY

from models.system_model_v3.model.state_variables.system import stability_fee
from models.system_model_v3.model.state_variables.historical_state import env_process_df, eth_price_mean, eth_returns_mean, market_price_mean


'''
See https://medium.com/reflexer-labs/introducing-proto-rai-c4cf1f013ef for current/launch values
'''


# TODO: Default assumption, set according to process for deriving per-second alpha
halflife = SPY / 52 # weeklong halflife
alpha = int(np.power(.5, float(1 / halflife)) * RAY)

'''
Deliverables:
Sweep of alpha
Kp
Ki
liquidation_ratio
liquidity threshold
TWAP:
window_size=15*3600, # 15 hours
granularity=5

max_window_size=21*3600, # 21 hours

Metrics:
liquidity threshold: (metric + deliverable) reserves of RAI in Uniswap (as fraction of total supply)

debt_ceiling setter

Control period 3 hours
TWAP 6 hours
'''



params = {
    # Admin parameters
    'debug': [True], # Print debug messages (see APT model)
    'raise_on_assert': [True], # See assert_log() in utils.py
    'free_memory_states': [['cdps', 'events', 'uniswap_oracle']],

    # Configuration options
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],

    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_price': [lambda timestep, df=env_process_df: df.iloc[timestep].Open],
    'seconds_passed': [lambda timestep, df=env_process_df: df.iloc[timestep].seconds_passed],

    # Time parameters
    'expected_blocktime': [15], # seconds
    # TODO: implement control period
    'minumum_control_period': [lambda _timestep: 3600], # seconds
    'expected_control_delay': [lambda _timestep: 1200], # seconds
    
    # Controller parameters
    'controller_enabled': [False],
    'kp': [5e-7], # proportional term for the stability controller: units 1/USD
    'ki': [lambda control_period=3600: -1e-7 / control_period], # integral term for the stability controller: units 1/(USD*seconds)
    'alpha': [alpha], # in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    
    # APT model
    'interest_rate': [1.03], # Real-world expected interest rate, for determining profitable arbitrage opportunities
    'eth_price_mean': [eth_price_mean],
    'eth_returns_mean': [eth_returns_mean],
    'market_price_mean': [market_price_mean],

    # APT OLS model
    'alpha_0': [0],
    'alpha_1': [1],
    'beta_0': [1.0003953223600617],
    'beta_1': [0.6756295152422528],
    'beta_2': [3.86810578185312e-06],

    # CDP parameters
    'liquidation_ratio': [1.5], # Configure the liquidation ratio parameter e.g. 150%
    'liquidation_buffer': [2.0], # Configure the liquidation buffer parameter: the multiplier for the liquidation ratio, that users apply as a buffer
    'liquidation_penalty': [0], # Percentage added on top of collateral needed to liquidate CDP. This is needed in order to avoid auction grinding attacks.
    'debt_ceiling': [1e9],

    # System parameters
    'stability_fee': [lambda timestep, df=None: stability_fee], # per second interest rate (x% per month)

    # Uniswap parameters
    'uniswap_fee': [0.003], # 0.3%
    'gas_price': [100e-9], # 100 gwei, current "fast" transaction
    'swap_gas_used': [133340],
    'cdp_gas_used': [133340],
}