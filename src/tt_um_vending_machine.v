`timescale 1ns/1ps
`default_nettype none

module tt_um_vending_machine (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    wire coin_1k = ui_in[0];
    wire coin_2k = ui_in[1];
    wire coin_5k = ui_in[2];
    wire cancel  = ui_in[3];

    // Chỉ chấp nhận đúng 1 loại tiền tại một thời điểm
    wire valid_coin;

    assign valid_coin =
           (ui_in[2:0] == 3'b001) ||
           (ui_in[2:0] == 3'b010) ||
           (ui_in[2:0] == 3'b100);

    localparam S0 = 3'd0;
    localparam S1 = 3'd1;
    localparam S2 = 3'd2;
    localparam S3 = 3'd3;
    localparam S4 = 3'd4;

    reg [2:0] current_state;
    reg [2:0] next_state;

    reg       dispense_reg;
    reg [6:0] change_reg;

    reg       dispense_next;
    reg [6:0] change_next;

    /*
     * State register + output register
     */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= S0;
            dispense_reg  <= 1'b0;
            change_reg    <= 7'd0;
        end
        else if (ena) begin
            current_state <= next_state;
            dispense_reg  <= dispense_next;
            change_reg    <= change_next;
        end
    end

    /*
     * Next-state logic
     */
    always @(*) begin

        // Mặc định giữ trạng thái
        next_state = current_state;

        // Output mặc định tắt
        dispense_next = 1'b0;
        change_next   = 7'd0;

        /*
         * CANCEL có độ ưu tiên cao nhất
         */
        if (cancel) begin

            dispense_next = 1'b0;

            case (current_state)
                S0: change_next = 7'd0;
                S1: change_next = 7'd1;
                S2: change_next = 7'd2;
                S3: change_next = 7'd3;
                S4: change_next = 7'd4;
                default: change_next = 7'd0;
            endcase

            next_state = S0;
        end

        /*
         * Chỉ xử lý khi coin input hợp lệ
         */
        else if (valid_coin) begin

            case (current_state)

                // =========================
                // Đang có 0k
                // =========================
                S0: begin
                    if (coin_1k)
                        next_state = S1;

                    else if (coin_2k)
                        next_state = S2;

                    else if (coin_5k) begin
                        dispense_next = 1'b1;
                        change_next   = 7'd0;
                        next_state    = S0;
                    end
                end

                // =========================
                // Đang có 1k
                // =========================
                S1: begin
                    if (coin_1k)
                        next_state = S2;

                    else if (coin_2k)
                        next_state = S3;

                    else if (coin_5k) begin
                        // 1k + 5k = 6k
                        dispense_next = 1'b1;
                        change_next   = 7'd1;
                        next_state    = S0;
                    end
                end

                // =========================
                // Đang có 2k
                // =========================
                S2: begin
                    if (coin_1k)
                        next_state = S3;

                    else if (coin_2k)
                        next_state = S4;

                    else if (coin_5k) begin
                        // 2k + 5k = 7k
                        dispense_next = 1'b1;
                        change_next   = 7'd2;
                        next_state    = S0;
                    end
                end

                // =========================
                // Đang có 3k
                // =========================
                S3: begin
                    if (coin_1k)
                        next_state = S4;

                    else if (coin_2k) begin
                        // 3k + 2k = 5k
                        dispense_next = 1'b1;
                        change_next   = 7'd0;
                        next_state    = S0;
                    end

                    else if (coin_5k) begin
                        // 3k + 5k = 8k
                        dispense_next = 1'b1;
                        change_next   = 7'd3;
                        next_state    = S0;
                    end
                end

                // =========================
                // Đang có 4k
                // =========================
                S4: begin
                    if (coin_1k) begin
                        // 4k + 1k = 5k
                        dispense_next = 1'b1;
                        change_next   = 7'd0;
                        next_state    = S0;
                    end

                    else if (coin_2k) begin
                        // 4k + 2k = 6k
                        dispense_next = 1'b1;
                        change_next   = 7'd1;
                        next_state    = S0;
                    end

                    else if (coin_5k) begin
                        // 4k + 5k = 9k
                        dispense_next = 1'b1;
                        change_next   = 7'd4;
                        next_state    = S0;
                    end
                end

                default: begin
                    next_state = S0;
                end

            endcase
        end

        /*
         * Nếu:
         * ui_in[2:0] = 000
         * hoặc input coin không hợp lệ như 011, 101, 110, 111
         *
         * => giữ nguyên trạng thái
         */
    end

    assign uo_out = {change_reg, dispense_reg};

endmodule

`default_nettype wire