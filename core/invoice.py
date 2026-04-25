"""
core/invoice.py — GST-compliant PDF invoice generator for Aurus Jewels.
"""
import os, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from database.db import execute_write

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer, HRFlowable
    )
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


def generate_invoice_number(order_id: int) -> str:
    now = datetime.datetime.now()
    return "AJ" + now.strftime("%Y%m") + "-" + str(order_id).zfill(5)


def _r(amount) -> str:
    """Format amount as Rs. X,XX,XXX.XX using Indian numbering."""
    try:
        val = float(amount)
        # Indian number format: last 3 digits, then groups of 2
        negative = val < 0
        val = abs(val)
        s = f"{val:.2f}"
        integer_part, decimal_part = s.split(".")
        # Apply Indian grouping
        if len(integer_part) <= 3:
            formatted = integer_part
        else:
            last3 = integer_part[-3:]
            remaining = integer_part[:-3]
            groups = []
            while len(remaining) > 2:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            if remaining:
                groups.append(remaining)
            groups.reverse()
            formatted = ",".join(groups) + "," + last3
        result = "Rs." + formatted + "." + decimal_part
        return ("-" + result) if negative else result
    except Exception:
        return "Rs.0.00"


def generate_invoice_pdf(
    order: dict,
    items: list,
    customer: dict,
    address: dict
) -> str | None:
    if not REPORTLAB_OK:
        return None

    os.makedirs(config.INVOICE_DIR, exist_ok=True)
    inv_no   = generate_invoice_number(order["order_id"])
    filepath = os.path.join(config.INVOICE_DIR, inv_no + ".pdf")

    # ── Colours ──────────────────────────────────────────────
    GOLD  = colors.HexColor("#B8860B")
    CREAM = colors.HexColor("#FFF8EE")
    ESP   = colors.HexColor("#1A1008")
    MOC   = colors.HexColor("#8B6914")
    LIGHT = colors.HexColor("#F5E6C8")
    WHITE = colors.white

    # ── Styles ───────────────────────────────────────────────
    brand_s = ParagraphStyle(
        "brand", fontName="Helvetica-Bold",
        fontSize=16, textColor=GOLD,
        spaceAfter=3, spaceBefore=0
    )
    tagline_s = ParagraphStyle(
        "tagline", fontName="Helvetica",
        fontSize=8, textColor=MOC,
        spaceAfter=2
    )
    meta_s = ParagraphStyle(
        "meta", fontName="Helvetica",
        fontSize=7.5, textColor=MOC,
        spaceAfter=0
    )
    h2_s = ParagraphStyle(
        "h2", fontName="Helvetica-Bold",
        fontSize=9, textColor=ESP,
        spaceAfter=4
    )
    body_s = ParagraphStyle(
        "body", fontName="Helvetica",
        fontSize=8.5, textColor=ESP,
        spaceAfter=2, leading=13
    )
    small_s = ParagraphStyle(
        "small", fontName="Helvetica",
        fontSize=7.5, textColor=MOC,
        spaceAfter=1, leading=11
    )
    right_s = ParagraphStyle(
        "right", fontName="Helvetica-Bold",
        fontSize=11, textColor=ESP,
        alignment=TA_RIGHT
    )
    right_small_s = ParagraphStyle(
        "right_small", fontName="Helvetica",
        fontSize=8, textColor=MOC,
        alignment=TA_RIGHT
    )

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin    = 14 * mm,
        bottomMargin = 14 * mm,
        leftMargin   = 16 * mm,
        rightMargin  = 16 * mm,
    )
    story = []

    # ── Header: brand left, invoice title right ───────────────
    header_data = [[
        # LEFT: brand block
        [
            Paragraph("AURUS JEWELS", brand_s),
            Paragraph("Fine Hallmarked Gold &amp; Silver Jewellery", tagline_s),
            Paragraph("GSTIN: " + config.GSTIN, meta_s),
            Paragraph(config.BUSINESS_ADDR, meta_s),
        ],
        # RIGHT: invoice label
        [
            Paragraph("TAX INVOICE", right_s),
            Paragraph("GST Compliant Document", right_small_s),
        ]
    ]]
    header_tbl = Table(header_data, colWidths=[120*mm, 54*mm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=4))

    # ── Invoice meta ─────────────────────────────────────────
    meta_rows = [
        ["Invoice No:", inv_no,         "Order ID:",   "#" + str(order["order_id"])],
        ["Date:",       datetime.datetime.now().strftime("%d %b %Y"),
         "Status:",     str(order.get("order_status","confirmed")).upper()],
    ]
    meta_tbl = Table(meta_rows, colWidths=[28*mm, 58*mm, 28*mm, 58*mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",       (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",       (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 8.5),
        ("TEXTCOLOR",      (0,0), (-1,-1), ESP),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [CREAM, WHITE]),
        ("PADDING",        (0,0), (-1,-1), 4),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 5*mm))

    # ── Bill To / Ship To ────────────────────────────────────
    ship = address or {}
    line2 = ship.get("address_line2","") or ""
    ship_addr = ship.get("address_line1","")
    if line2:
        ship_addr += ", " + line2

    bs_data = [[
        [
            Paragraph("<b>Bill To</b>", h2_s),
            Paragraph(customer.get("full_name",""), body_s),
            Paragraph(customer.get("email",""), small_s),
            Paragraph(customer.get("phone","") or "", small_s),
        ],
        [
            Paragraph("<b>Ship To</b>", h2_s),
            Paragraph(ship.get("full_name",""), body_s),
            Paragraph(ship_addr, small_s),
            Paragraph(
                str(ship.get("city","")) + " - " + str(ship.get("pincode","")),
                small_s
            ),
        ]
    ]]
    bs_tbl = Table(bs_data, colWidths=[87*mm, 87*mm])
    bs_tbl.setStyle(TableStyle([
        ("VALIGN",   (0,0), (-1,-1), "TOP"),
        ("PADDING",  (0,0), (-1,-1), 4),
        ("BOX",      (0,0), (0,-1), 0.5, colors.HexColor("#E8D5A3")),
        ("BOX",      (1,0), (1,-1), 0.5, colors.HexColor("#E8D5A3")),
        ("BACKGROUND",(0,0),(0,-1), CREAM),
        ("BACKGROUND",(1,0),(1,-1), WHITE),
    ]))
    story.append(bs_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Items table ──────────────────────────────────────────
    story.append(Paragraph("Items Ordered", h2_s))

    col_w = [x*mm for x in [7, 44, 11, 11, 16, 17, 16, 16, 13, 18]]
    header_row = ["#", "Product", "Karat", "Wt(g)",
                  "Rate/g", "Metal", "Making",
                  "Pre-GST", "GST 5%", "Total"]
    rows = [header_row]

    for i, item in enumerate(items, 1):
        rows.append([
            str(i),
            str(item.get("product_name","")),
            str(item.get("karat","")),
            str(round(float(item.get("weight_g",0)), 3)),
            _r(item.get("gold_rate_used",0)),
            _r(item.get("metal_value",0)),
            _r(item.get("making_charge",0)),
            _r(item.get("pre_gst_amount",0)),
            _r(item.get("gst_amount",0)),
            _r(item.get("line_total",0)),
        ])

    items_tbl = Table(rows, colWidths=col_w)
    items_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0),  GOLD),
        ("TEXTCOLOR",      (0,0), (-1,0),  WHITE),
        ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",       (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0), (-1,-1), 7.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, CREAM]),
        ("GRID",           (0,0), (-1,-1), 0.3, colors.HexColor("#E8D5A3")),
        ("PADDING",        (0,0), (-1,-1), 4),
        ("ALIGN",          (3,0), (-1,-1), "RIGHT"),
        ("ALIGN",          (0,0), (0,-1),  "CENTER"),
        ("ALIGN",          (2,0), (2,-1),  "CENTER"),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("WORDWRAP",       (1,0), (1,-1),  True),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 4*mm))

    # ── GST Breakdown box ─────────────────────────────────────
    taxable = float(order.get("subtotal",0)) - float(order.get("loyalty_discount",0) or 0) - float(order.get("coupon_discount",0) or 0)
    cgst    = float(order.get("cgst_amount",0))
    sgst    = float(order.get("sgst_amount",0))

    gst_data = [
        [Paragraph("<b>GST Breakdown</b>", h2_s), "", "", ""],
        ["Taxable Value", "CGST @ 2.5%", "SGST @ 2.5%", "Total GST"],
        [_r(taxable), _r(cgst), _r(sgst), _r(cgst + sgst)],
    ]
    gst_tbl = Table(gst_data, colWidths=[43*mm, 43*mm, 43*mm, 43*mm])
    gst_tbl.setStyle(TableStyle([
        ("SPAN",           (0,0), (-1,0)),
        ("BACKGROUND",     (0,1), (-1,1), CREAM),
        ("FONTNAME",       (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTNAME",       (0,2), (-1,2), "Helvetica"),
        ("FONTSIZE",       (0,0), (-1,-1), 8),
        ("TEXTCOLOR",      (0,1), (-1,2), ESP),
        ("ALIGN",          (0,2), (-1,2), "CENTER"),
        ("ALIGN",          (0,1), (-1,1), "CENTER"),
        ("GRID",           (0,1), (-1,-1), 0.3, colors.HexColor("#E8D5A3")),
        ("PADDING",        (0,0), (-1,-1), 4),
        ("BOX",            (0,0), (-1,-1), 0.5, colors.HexColor("#E8D5A3")),
        ("BACKGROUND",     (0,0), (-1,0), CREAM),
    ]))
    story.append(gst_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Totals ───────────────────────────────────────────────
    totals_rows = [
        ["Subtotal",         _r(order.get("subtotal",0))],
    ]
    coup = float(order.get("coupon_discount",0) or 0)
    loy  = float(order.get("loyalty_discount",0) or 0)
    if coup > 0:
        totals_rows.append(["Coupon Discount", "-" + _r(coup)])
    if loy > 0:
        totals_rows.append(["Loyalty Discount", "-" + _r(loy)])
    totals_rows += [
        ["CGST (2.5%)",  _r(cgst)],
        ["SGST (2.5%)",  _r(sgst)],
        ["TOTAL AMOUNT", _r(order.get("total_amount",0))],
    ]

    totals_tbl = Table(totals_rows, colWidths=[130*mm, 44*mm], hAlign="RIGHT")
    n = len(totals_rows)
    totals_tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,n-2), "Helvetica"),
        ("FONTNAME",       (0,n-1), (-1,n-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,n-2), 8.5),
        ("FONTSIZE",       (0,n-1), (-1,n-1), 10),
        ("TEXTCOLOR",      (0,n-1), (-1,n-1), GOLD),
        ("TEXTCOLOR",      (0,0), (-1,n-2), ESP),
        ("ALIGN",          (1,0), (1,-1),  "RIGHT"),
        ("LINEABOVE",      (0,n-1), (-1,n-1), 1, GOLD),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, CREAM]),
        ("PADDING",        (0,0), (-1,-1), 4),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 5*mm))

    # ── Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT, spaceAfter=4))

    footer_data = [[
        Paragraph(
            "All products are BIS hallmarked. Prices calculated live from the official "
            "IBJA gold rate. GST split as CGST 2.5% + SGST 2.5%. "
            "This is a computer-generated invoice.",
            small_s
        ),
        [
            Paragraph("For Aurus Jewels", small_s),
            Spacer(1, 10*mm),
            Paragraph("Authorised Signatory", small_s),
        ]
    ]]
    footer_tbl = Table(footer_data, colWidths=[120*mm, 54*mm])
    footer_tbl.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 2),
        ("ALIGN",   (1,0), (1,-1),  "RIGHT"),
    ]))
    story.append(footer_tbl)

    doc.build(story)
    return filepath


def save_invoice_path(order_id: int, invoice_number: str, filepath: str):
    execute_write(
        "UPDATE fact_orders SET invoice_number=%s, invoice_path=%s WHERE order_id=%s",
        (invoice_number, filepath, order_id)
    )