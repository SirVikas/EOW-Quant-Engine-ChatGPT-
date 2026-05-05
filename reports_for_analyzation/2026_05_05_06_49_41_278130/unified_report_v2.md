# Unified report error

```
Traceback (most recent call last):
  File "D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\main.py", line 5286, in download_report_bundle
    unified_v2_md = generate_full_report_v2(_v2_data)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\core\reporting\unified_report_engine_v2.py", line 1048, in generate_full_report_v2
    _s5_capital_efficiency(data),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\core\reporting\unified_report_engine_v2.py", line 356, in _s5_capital_efficiency
    ("Daily Risk Remaining",  f"${daily_rem * (equity if daily_rem < 1 else 1):.2f}" if daily_rem < 1 else f"{_pct(daily_rem * 100)} of equity"),
                                                                                        ^^^^^^^^^^^^^
TypeError: '<' not supported between instances of 'NoneType' and 'int'

```
