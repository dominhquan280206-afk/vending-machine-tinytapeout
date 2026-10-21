<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->


## External hardware

List external hardware used in your project (e.g. PMOD, LED display, etc), if any
## How it works

This project implements a finite state machine (FSM) for a vending machine with a product price of 5,000 VND.

The machine accepts three coin values through the input pins:

- `ui_in[0]`: 1,000 VND
- `ui_in[1]`: 2,000 VND
- `ui_in[2]`: 5,000 VND
- `ui_in[3]`: Cancel transaction

Only valid one-hot coin inputs are accepted. If multiple coin inputs are active at the same time, the invalid coin input is ignored. If the cancel input is active, cancellation has priority over coin insertion.

The FSM keeps track of the accumulated credit. When the total credit reaches or exceeds 5,000 VND, `uo_out[0]` is asserted to dispense the product.

Any excess credit is returned through `uo_out[7:1]`. The value represents the change in units of 1,000 VND.

If the user cancels the transaction before purchasing, the current accumulated credit is returned through `uo_out[7:1]` and no product is dispensed.

The design uses an active-low reset (`rst_n`). The FSM only processes transactions when `ena` is high.


## How to test

The design is verified using a Cocotb testbench with Icarus Verilog.

The verification covers the following cases:

1. Exact payment: 2k + 1k + 2k = 5k.
2. Overpayment: 2k + 5k = 7k, with 2k returned as change.
3. Cancellation after inserting 3k.
4. Continuous coin insertion: 2k + 2k + 5k = 9k, with 4k returned as change.
5. Invalid one-hot coin input.
6. Cancel and coin asserted simultaneously, with cancel taking priority.
7. Cancel with zero accumulated credit.
8. Direct payment using a 5k coin.
9. Reset during a transaction.
10. Enable control using `ena`.

To run the RTL simulation locally:

    cd test
    make

A successful simulation reports:

    ALL F02 TESTS PASSED
    TESTS=1 PASS=1 FAIL=0

The GitHub Actions flow also performs gate-level verification after synthesis.
