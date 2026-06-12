from odoo import fields, models


class OverReceiptWizard(models.TransientModel):
    _name = "over.receipt.wizard"
    _description = "Over Receipt Warning"

    picking_id = fields.Many2one( "stock.picking", required=True,)
    message = fields.Text( readonly=True, )
    def action_continue(self):
        return (
            self.picking_id
            .with_context( skip_over_receipt_popup=True )
            .button_validate())
    
    def action_cancel(self):

        for move in self.picking_id.move_ids:
            move.write({"quantity": move.product_uom_qty})
        return {"type": "ir.actions.act_window_close"}