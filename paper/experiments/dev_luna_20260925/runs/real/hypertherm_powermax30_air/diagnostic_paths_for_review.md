# Extracted diagnostic paths for expert review

Automatically extracted, not expert-approved. Source page numbers are physical PDF pages.

## Path 1

```json
{
  "indicator_type": "ErrorCode",
  "indicator": "Error LED blink code",
  "failure_mode": "Faulty fan, solenoid valve, or power board",
  "corrective_action": "Replace the fan",
  "indicator_context": "Error LED blink code The Error LED blinks four times between pauses. 4 blinks The Error LED blinks four times between pauses. err_4_blinks_161c629b3a76a22f6d8097618ac3b4a55b0e788530064c66a97160a799fa7911 Error LED blink code Faulty fan, solenoid valve, or power board",
  "failure_mode_context": "Faulty fan, solenoid valve, or power board The fan, solenoid valve, or power board is faulty. The fan, solenoid valve, or power board is faulty. fm_faulty_fan_solenoid_valve_or_power_board_97b9ac69c963ce1b4fd20475aed3b384f12ada618b6af4a3ec29c776450e6881 asset_level Faulty fan, solenoid valve, or power board Faulty fan, solenoid valve, or power board if Test 8 fails, replace the fan. Faulty fan, solenoid valve, or power board",
  "corrective_action_context": "Replace the fan Replace the fan if Test 8 fails. ca_replace_the_fan_11f19eb88a55ca564e8f6531b4a8ea625d34eb2b8288d5beccf61305352e6c8d replacement Replace the fan if Test 8 fails. If Test 8 fails, replace the fan. Replace the fan typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF if Test 8 fails, replace the fan. Faulty fan, solenoid valve, or power board",
  "pages": [
    77
  ],
  "indicator_id": "err_4_blinks_161c629b3a76a22f6d8097618ac3b4a55b0e788530064c66a97160a799fa7911",
  "failure_mode_id": "fm_faulty_fan_solenoid_valve_or_power_board_97b9ac69c963ce1b4fd20475aed3b384f12ada618b6af4a3ec29c776450e6881",
  "corrective_action_id": "ca_replace_the_fan_11f19eb88a55ca564e8f6531b4a8ea625d34eb2b8288d5beccf61305352e6c8d",
  "branch_lineage_id": "dbranch_1c0d54baaf0f2b73d15b92ec0466457f213a6904aaa2fef0f79dd02ff3526d6f"
}
```

## Path 2

```json
{
  "indicator_type": "Symptom",
  "indicator": "Control board Reset LED illuminates",
  "failure_mode": "Incorrect power board voltages",
  "corrective_action": "Replace the power board",
  "indicator_context": "Control board Reset LED illuminates The control board’s Reset LED illuminates. The control board’s Reset LED illuminates. Control board Reset LED illuminates Medium sym_control_board_reset_led_illuminates_2ef433e29653248ffc760d26efe5d9364085059fd076209be60e5493ee6cbedc the voltages on the power board may be incorrect",
  "failure_mode_context": "Incorrect power board voltages The voltages on the power board may be incorrect. The voltages on the power board may be incorrect. fm_incorrect_power_board_voltages_d98bf7ed0987f10f3a5f996b0c86e5db270cb3761ac81647c214b94df0c55268 asset_level Incorrect power board voltages the voltages on the power board may be incorrect Otherwise, replace the power board. the voltages on the power board may be incorrect",
  "corrective_action_context": "Replace the power board Replace the power board if the values remain incorrect after the ribbon cable is detached. ca_replace_the_power_board_9704ca6054e05d84c8a4693262249424cde74b62658b00c0516c6c9522502077 replacement Replace the power board if the values remain incorrect after the ribbon cable is detached. Otherwise, replace the power board. Replace the power board typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF Otherwise, replace the power board. the voltages on the power board may be incorrect",
  "pages": [
    76
  ],
  "indicator_id": "sym_control_board_reset_led_illuminates_2ef433e29653248ffc760d26efe5d9364085059fd076209be60e5493ee6cbedc",
  "failure_mode_id": "fm_incorrect_power_board_voltages_d98bf7ed0987f10f3a5f996b0c86e5db270cb3761ac81647c214b94df0c55268",
  "corrective_action_id": "ca_replace_the_power_board_9704ca6054e05d84c8a4693262249424cde74b62658b00c0516c6c9522502077",
  "branch_lineage_id": "dbranch_91edd7aa4bfde8f04199b767bf756da2f5116b98daf0d081f159f8e85e29be89"
}
```

## Path 3

```json
{
  "indicator_type": "Symptom",
  "indicator": "Low air pressure",
  "failure_mode": "Torch O-ring is dry",
  "corrective_action": "Apply silicone lubricant to the O-ring and threads",
  "indicator_context": "Low air pressure Low air pressure troubleshooting branch for a dry torch O-ring. Low air pressure troubleshooting branch for a dry torch O-ring. Low air pressure Medium sym_low_air_pressure_1822567453d819ca4ed16dbbc6cf26238dd14ee5ef9d4e00150b269f884f08ec If the torch O-ring is dry",
  "failure_mode_context": "Torch O-ring is dry The torch O-ring is dry. The torch O-ring is dry. fm_torch_o_ring_is_dry_475b360e6b9ec4e53006f95c5a7eb63f14c7fb4cf4a088817abe206c2d9ce770 comp_torch_o_ring_6bdaf6ee9698c306841bbb04f43ba3d9781ed500c180a50002f3d5770adef67d Torch O-ring is dry If the torch O-ring is dry If the torch O-ring is dry, apply a thin film of silicone lubricant (027055) on the O-ring and the threads.",
  "corrective_action_context": "Apply silicone lubricant to the O-ring and threads Apply a thin film of silicone lubricant. ca_apply_silicone_lubricant_to_the_o_ring_and_threa_da117f38568d28cc65d1affe43543e203b8c3b28a68e8c27a9bf2371f889b7db lubrication Apply a thin film of silicone lubricant. apply a thin film of silicone lubricant (027055) on the O-ring and the threads. Apply silicone lubricant to the O-ring and threads typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF If the torch O-ring is dry, apply a thin film of silicone lubricant (027055) on the O-ring and the threads.",
  "pages": [
    101
  ],
  "indicator_id": "sym_low_air_pressure_1822567453d819ca4ed16dbbc6cf26238dd14ee5ef9d4e00150b269f884f08ec",
  "failure_mode_id": "fm_torch_o_ring_is_dry_475b360e6b9ec4e53006f95c5a7eb63f14c7fb4cf4a088817abe206c2d9ce770",
  "corrective_action_id": "ca_apply_silicone_lubricant_to_the_o_ring_and_threa_da117f38568d28cc65d1affe43543e203b8c3b28a68e8c27a9bf2371f889b7db",
  "branch_lineage_id": "dbranch_e68d3612b1c008415e026dca098c5650a40c295c86f747dd97fdbe7c6ca0f96b"
}
```

## Path 4

```json
{
  "indicator_type": "Symptom",
  "indicator": "Low pressure persists after completing the checks",
  "failure_mode": "Internal air compressor may be faulty",
  "corrective_action": "Install a new air compressor",
  "indicator_context": "Low pressure persists after completing the checks The low pressure issue persists after all checks are completed. The low pressure issue persists after all checks are completed. Low pressure persists after completing the checks Medium sym_low_pressure_persists_after_completing_the_check_c2807b11bd1189b9f2451759908a479fb526692399ee9726f8ca08e37b3fa197 If low pressure persists after you complete all of these checks",
  "failure_mode_context": "Internal air compressor may be faulty The internal air compressor may be faulty. The internal air compressor may be faulty. fm_internal_air_compressor_may_be_faulty_a53793ea47d085f0bea54078ed8a1682990b6d1438de4e62575efca52b6c6bb4 comp_internal_air_compressor_d2429d739187f9e15f3a100d4253dc92c7e7dc94d0bb37a22f22ac2aafb62c54 Internal air compressor may be faulty If low pressure persists after you complete all of these checks If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new air compressor.",
  "corrective_action_context": "Install a new air compressor Install a new air compressor. ca_install_a_new_air_compressor_4c48b70a861b46ff4e6b78ca5133d57d83a90461e5c87a7f73277cd13e17f946 replacement Install a new air compressor. Install a new air compressor. See page 169. Install a new air compressor typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new air compressor.",
  "pages": [
    103
  ],
  "indicator_id": "sym_low_pressure_persists_after_completing_the_check_c2807b11bd1189b9f2451759908a479fb526692399ee9726f8ca08e37b3fa197",
  "failure_mode_id": "fm_internal_air_compressor_may_be_faulty_a53793ea47d085f0bea54078ed8a1682990b6d1438de4e62575efca52b6c6bb4",
  "corrective_action_id": "ca_install_a_new_air_compressor_4c48b70a861b46ff4e6b78ca5133d57d83a90461e5c87a7f73277cd13e17f946",
  "branch_lineage_id": "dbranch_76a6cf7484f4cb29c172444b9724954bb9520fca80fe82cc6d559c1c9b48ef43"
}
```

## Path 5

```json
{
  "indicator_type": "Symptom",
  "indicator": "Low pressure persists",
  "failure_mode": "Faulty internal air compressor",
  "corrective_action": "Install a new air compressor",
  "indicator_context": "Low pressure persists Low pressure continues after all preceding checks. Low pressure continues after all preceding checks. Low pressure persists Medium sym_low_pressure_persists_fe4c631e13cbf99e750addd078bf06620dcc02a04f0183134de37ddb8a827bc6 the internal air compressor may be faulty",
  "failure_mode_context": "Faulty internal air compressor The internal air compressor may be faulty when low pressure persists after the checks. The internal air compressor may be faulty when low pressure persists after the checks. fm_faulty_internal_air_compressor_7700b0587e42937db9d8bba900ce125397e172545e1dac073b68533c37564cd9 comp_internal_air_compressor_d2429d739187f9e15f3a100d4253dc92c7e7dc94d0bb37a22f22ac2aafb62c54 Faulty internal air compressor the internal air compressor may be faulty Install a new air compressor.",
  "corrective_action_context": "Install a new air compressor Replace the internal air compressor. ca_install_a_new_air_compressor_2e8a152b3b6c7b27b044a2c95013a109edd8ae5353d44b38adc5c04b77694875 replacement Replace the internal air compressor. Install a new air compressor. Install a new air compressor typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF Install a new air compressor.",
  "pages": [
    103
  ],
  "indicator_id": "sym_low_pressure_persists_fe4c631e13cbf99e750addd078bf06620dcc02a04f0183134de37ddb8a827bc6",
  "failure_mode_id": "fm_faulty_internal_air_compressor_7700b0587e42937db9d8bba900ce125397e172545e1dac073b68533c37564cd9",
  "corrective_action_id": "ca_install_a_new_air_compressor_2e8a152b3b6c7b27b044a2c95013a109edd8ae5353d44b38adc5c04b77694875",
  "branch_lineage_id": "dbranch_2d7e39d17c055af1a86d2923321ade0c6cf7ba5b812199375779f1fb11aa2988"
}
```

## Path 6

```json
{
  "indicator_type": "Symptom",
  "indicator": "No gas flows when torch trigger is pulled",
  "failure_mode": "Damaged torch or torch lead prevents the start signal from reaching the control board",
  "corrective_action": "Inspect and replace torch or torch lead if necessary",
  "indicator_context": "No gas flows when torch trigger is pulled The power ON LED illuminates, but no fault LEDs illuminate, and no gas flows when you pull the torch trigger. The power ON LED illuminates, but no fault LEDs illuminate, and no gas flows when you pull the torch trigger. No gas flows when torch trigger is pulled High sym_no_gas_flows_when_torch_trigger_is_pulled_716c7b8f4c1bef020158e743be52e07780db7c19bf1b5368f3c231d1767247d9 Damaged torch or torch lead The start signal is not reaching the control board due to:",
  "failure_mode_context": "Damaged torch or torch lead prevents the start signal from reaching the control board The start signal is not reaching the control board due to a damaged torch or torch lead. The start signal is not reaching the control board due to a damaged torch or torch lead. fm_damaged_torch_or_torch_lead_prevents_the_start_s_da8d6731e6dc58d3f3f17e81d1ea377566005c444e6484d6834895b452a0a6ee comp_torch_or_torch_lead_ffa16620556d3337c106187e82534a19427dd7710955cdadb9754e3098b1cb08 Damaged torch or torch lead prevents the start signal from reaching the control board Damaged torch or torch lead The start signal is not reaching the control board due to: Inspect the torch and torch lead, and replace if necessary. Damaged torch or torch lead",
  "corrective_action_context": "Inspect and replace torch or torch lead if necessary Inspect the torch and torch lead, and replace if necessary. ca_inspect_and_replace_torch_or_torch_lead_if_neces_f676cdb7c097884c4b376df7fffcf2bab338bacca299242f3d3123b41d25280c replacement Inspect the torch and torch lead, and replace if necessary. Inspect the torch and torch lead, and replace if necessary. Inspect and replace torch or torch lead if necessary typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF Inspect the torch and torch lead, and replace if necessary. Damaged torch or torch lead",
  "pages": [
    65
  ],
  "indicator_id": "sym_no_gas_flows_when_torch_trigger_is_pulled_716c7b8f4c1bef020158e743be52e07780db7c19bf1b5368f3c231d1767247d9",
  "failure_mode_id": "fm_damaged_torch_or_torch_lead_prevents_the_start_s_da8d6731e6dc58d3f3f17e81d1ea377566005c444e6484d6834895b452a0a6ee",
  "corrective_action_id": "ca_inspect_and_replace_torch_or_torch_lead_if_neces_f676cdb7c097884c4b376df7fffcf2bab338bacca299242f3d3123b41d25280c",
  "branch_lineage_id": "dbranch_2cfbcb549ef17d9ae04be6200d3bb85538b47d56631cb2d6aeeb7a2d43a1ed17"
}
```

## Path 7

```json
{
  "indicator_type": "Symptom",
  "indicator": "Step 7 and step 8 voltage values differ by more than 30 V",
  "failure_mode": "Power board voltage imbalance",
  "corrective_action": "Replace the power board",
  "indicator_context": "Step 7 and step 8 voltage values differ by more than 30 V The values found in step 7 and step 8 differ by more than 30 V. The values found in step 7 and step 8 differ by more than 30 V. Step 7 and step 8 voltage values differ by more than 30 V Medium sym_step_7_and_step_8_voltage_values_differ_by_more__52b170c228a163c73d0e0931a0426fafd9d31850604c44b8bf7095208f0e7905 If they differ by more than 30 V, replace the power board.",
  "failure_mode_context": "Power board voltage imbalance The values found in step 7 and step 8 differ by more than 30 V. The values found in step 7 and step 8 differ by more than 30 V. fm_power_board_voltage_imbalance_3662186169bd1cd4199b41f4f0b8cea1c3e9db43d5a00434757f71a036e98169 comp_power_board_4237efd53ce9075cd81c88e0d7c15b9b1a56807378ab7a7ca07c0c73140c7fde Power board voltage imbalance If they differ by more than 30 V, replace the power board. If they differ by more than 30 V, replace the power board.",
  "corrective_action_context": "Replace the power board Replace the power board. ca_replace_the_power_board_1656a164b76130ae85ae65c381fbd9cc5e52c0dfb068b04b0313325d7346efbb replacement Replace the power board. replace the power board Replace the power board typed_diagnostic_edge_evidence hypertherm_powermax30_air_service_manual_rev4_808850.pdf technical PDF If they differ by more than 30 V, replace the power board.",
  "pages": [
    88
  ],
  "indicator_id": "sym_step_7_and_step_8_voltage_values_differ_by_more__52b170c228a163c73d0e0931a0426fafd9d31850604c44b8bf7095208f0e7905",
  "failure_mode_id": "fm_power_board_voltage_imbalance_3662186169bd1cd4199b41f4f0b8cea1c3e9db43d5a00434757f71a036e98169",
  "corrective_action_id": "ca_replace_the_power_board_1656a164b76130ae85ae65c381fbd9cc5e52c0dfb068b04b0313325d7346efbb",
  "branch_lineage_id": "dbranch_c87d4ef8153acb62dc00bc70b60a09643d51c651d842ce42e17a6f5c9658bb76"
}
```
