
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


# ============================================================
# Helper functions
# ============================================================

async def reset_dut(dut):
    """Reset DUT về trạng thái ban đầu."""
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def apply_input(dut, value):
    """
    Đặt ui_in trước cạnh lên của clock,
    sau đó kiểm tra output sau cạnh lên.
    """
    await FallingEdge(dut.clk)
    dut.ui_in.value = value

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def clear_input(dut):
    await FallingEdge(dut.clk)
    dut.ui_in.value = 0


def dispense(dut):
    """uo_out[0] = tín hiệu nhả hàng."""
    return int(dut.uo_out.value) & 0x01


def change(dut):
    """uo_out[7:1] = tiền thối, đơn vị nghìn đồng."""
    return int(dut.uo_out.value) >> 1


# ============================================================
# Main verification
# ============================================================

@cocotb.test()
async def test_vending_machine(dut):

    dut._log.info("======================================")
    dut._log.info("F02 - FSM VENDING MACHINE VERIFICATION")
    dut._log.info("======================================")

    # Clock 10 us - 100 kHz
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # --------------------------------------------------------
    # TEST 1: Đủ tiền chẵn
    # 2k + 1k + 2k = 5k
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 1: Exact payment 2k + 1k + 2k")

    await apply_input(dut, 0b00000010)
    assert dispense(dut) == 0

    await apply_input(dut, 0b00000001)
    assert dispense(dut) == 0

    await apply_input(dut, 0b00000010)

    assert dispense(dut) == 1
    assert change(dut) == 0

    dut._log.info("TEST 1 PASS")

    # --------------------------------------------------------
    # TEST 2: Thừa tiền
    # 2k + 5k = 7k -> trả lại 2k
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 2: Overpayment 2k + 5k")

    await apply_input(dut, 0b00000010)
    await apply_input(dut, 0b00000100)

    assert dispense(dut) == 1
    assert change(dut) == 2

    dut._log.info("TEST 2 PASS")

    # --------------------------------------------------------
    # TEST 3: Hủy giữa chừng
    # 1k + 2k = 3k -> cancel -> trả lại 3k
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 3: Cancel transaction")

    await apply_input(dut, 0b00000001)
    await apply_input(dut, 0b00000010)
    await apply_input(dut, 0b00001000)

    assert dispense(dut) == 0
    assert change(dut) == 3

    dut._log.info("TEST 3 PASS")

    # --------------------------------------------------------
    # TEST 4: Bỏ tiền liên tục
    # 2k + 2k + 5k = 9k -> trả lại 4k
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 4: Continuous coin insertion")

    await apply_input(dut, 0b00000010)
    await apply_input(dut, 0b00000010)
    await apply_input(dut, 0b00000100)

    assert dispense(dut) == 1
    assert change(dut) == 4

    dut._log.info("TEST 4 PASS")

    # --------------------------------------------------------
    # TEST 5: One-hot không hợp lệ
    #
    # 1k -> invalid 011 -> giữ trạng thái
    # sau đó +2k +2k = 5k
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 5: Invalid one-hot input")

    await apply_input(dut, 0b00000001)
    await apply_input(dut, 0b00000011)

    assert dispense(dut) == 0
    assert change(dut) == 0

    await apply_input(dut, 0b00000010)
    assert dispense(dut) == 0

    await apply_input(dut, 0b00000010)

    assert dispense(dut) == 1
    assert change(dut) == 0

    dut._log.info("TEST 5 PASS")

    # --------------------------------------------------------
    # TEST 6: Cancel và coin đồng thời
    # Cancel phải được ưu tiên
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 6: Cancel priority")

    await apply_input(dut, 0b00000010)
    await apply_input(dut, 0b00001001)

    assert dispense(dut) == 0
    assert change(dut) == 2

    dut._log.info("TEST 6 PASS")

    # --------------------------------------------------------
    # TEST 7: Cancel tại S0
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 7: Cancel with zero credit")

    await apply_input(dut, 0b00001000)

    assert dispense(dut) == 0
    assert change(dut) == 0

    dut._log.info("TEST 7 PASS")

    # --------------------------------------------------------
    # TEST 8: Bỏ trực tiếp 5k
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 8: Direct 5k payment")

    await apply_input(dut, 0b00000100)

    assert dispense(dut) == 1
    assert change(dut) == 0

    dut._log.info("TEST 8 PASS")

    # --------------------------------------------------------
    # TEST 9: Reset giữa giao dịch
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 9: Reset during transaction")

    # Bỏ 2k
    await apply_input(dut, 0b00000010)

    # Reset giữa giao dịch
    await FallingEdge(dut.clk)

    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    await Timer(100, units="ns")

    assert dispense(dut) == 0
    assert change(dut) == 0

    dut.rst_n.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")

    # Sau reset chỉ mới bỏ 2k -> chưa đủ mua
    await apply_input(dut, 0b00000010)

    assert dispense(dut) == 0
    assert change(dut) == 0

    dut._log.info("TEST 9 PASS")

    # --------------------------------------------------------
    # TEST 10: ena = 0
    # Khi ena = 0, FSM không được nhận coin
    # --------------------------------------------------------
    await reset_dut(dut)

    dut._log.info("TEST 10: Enable control")

    await FallingEdge(dut.clk)

    dut.ena.value = 0
    dut.ui_in.value = 0b00000010

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")

    # Xóa input trước khi bật lại ena
    await FallingEdge(dut.clk)

    dut.ui_in.value = 0
    dut.ena.value = 1

    # Nếu 2k khi ena=0 bị bỏ qua,
    # 1k + 2k = 3k -> chưa đủ mua hàng.
    await apply_input(dut, 0b00000001)
    await apply_input(dut, 0b00000010)

    assert dispense(dut) == 0
    assert change(dut) == 0

    dut._log.info("TEST 10 PASS")

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------
    await clear_input(dut)

    dut._log.info("======================================")
    dut._log.info("ALL F02 TESTS PASSED")
    dut._log.info("======================================")
