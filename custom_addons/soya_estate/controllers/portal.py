from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from collections import defaultdict
from datetime import datetime


class SoyaPortalController(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        partner = user.partner_id

        if 'property_count' in counters:
            owner_properties = request.env['soya.property'].search([
                ('owner_id', '=', partner.id)
            ])
            values['property_count'] = len(owner_properties)

        if 'rental_count' in counters:
            current_rentals = request.env['soya.rental.contract'].search([
                ('tenant_id', '=', partner.id),
                ('state', '=', 'active')
            ])
            values['rental_count'] = len(current_rentals)

        if 'document_count' in counters:
            documents = request.env['soya.contract.document'].search([
                '|',
                ('contract_id.landlord_id', '=', partner.id),
                ('contract_id.tenant_id', '=', partner.id)
            ])
            values['document_count'] = len(documents)

        return values

    @http.route('/my/properties', type='http', auth='user', website=True)
    def portal_my_properties(self, **kw):
        user = request.env.user
        partner = user.partner_id
        
        properties = request.env['soya.property'].search([
            ('owner_id', '=', partner.id)
        ])

        values = {
            'properties': properties,
            'page_title': 'Mes Biens Immobiliers',
        }
        return request.render('soya_estate.portal_my_properties', values)

    @http.route('/my/properties/<model("soya.property"):property>', type='http', auth='user', website=True)
    def portal_property_details(self, property, **kw):
        user = request.env.user
        partner = user.partner_id
        
        if property.owner_id.id != partner.id:
            return request.redirect('/my')

        current_rental = request.env['soya.rental.contract'].search([
            ('property_id', '=', property.id),
            ('state', '=', 'active')
        ], limit=1)

        rental_history = request.env['soya.rental.contract'].search([
            ('property_id', '=', property.id),
            ('state', '!=', 'draft')
        ], order='start_date desc')

        documents = request.env['soya.contract.document'].search([
            ('contract_id.property_id', '=', property.id)
        ])

        values = {
            'property': property,
            'current_rental': current_rental,
            'rental_history': rental_history,
            'documents': documents,
            'page_title': property.name,
        }
        return request.render('soya_estate.portal_property_details', values)

    @http.route('/my/rentals', type='http', auth='user', website=True)
    def portal_my_rentals(self, **kw):
        user = request.env.user
        partner = user.partner_id
        
        current_rentals = request.env['soya.rental.contract'].search([
            ('tenant_id', '=', partner.id),
            ('state', '=', 'active')
        ])

        past_rentals = request.env['soya.rental.contract'].search([
            ('tenant_id', '=', partner.id),
            ('state', 'in', ['done', 'cancelled'])
        ], order='end_date desc')

        values = {
            'current_rentals': current_rentals,
            'past_rentals': past_rentals,
            'page_title': 'Mes Locations',
        }
        return request.render('soya_estate.portal_my_rentals', values)

    @http.route('/my/rentals/<model("soya.rental.contract"):rental>', type='http', auth='user', website=True)
    def portal_rental_details(self, rental, **kw):
        user = request.env.user
        partner = user.partner_id
        
        if rental.tenant_id.id != partner.id:
            return request.redirect('/my/rentals')

        documents = request.env['soya.contract.document'].search([
            ('contract_id', '=', rental.id)
        ])

        payments = request.env['soya.payment'].search([
            ('contract_id', '=', rental.id)
        ], order='payment_date desc')

        values = {
            'rental': rental,
            'documents': documents,
            'payments': payments,
            'page_title': f"Location - {rental.property_id.name}",
        }
        return request.render('soya_estate.portal_rental_details', values)

    @http.route('/my/documents', type='http', auth='user', website=True)
    def portal_my_documents(self, **kw):
        user = request.env.user
        partner = user.partner_id
        
        documents = request.env['soya.contract.document'].search([
            ('contract_id.landlord_id', '=', partner.id)
        ], order='upload_date desc')

        documents_by_type = defaultdict(list)
        for doc in documents:
            documents_by_type[doc.document_type].append(doc)

        values = {
            'documents': documents,
            'documents_by_type': dict(documents_by_type),
            'page_title': 'Mes Documents',
        }
        return request.render('soya_estate.portal_my_documents', values)

    @http.route('/my/documents/<model("soya.contract.document"):document>/download', type='http', auth='user', website=True)
    def portal_document_download(self, document, **kw):
        user = request.env.user
        partner = user.partner_id
        
        is_landlord = document.contract_id.landlord_id.id == partner.id
        is_tenant = document.contract_id.tenant_id.id == partner.id
        
        if not (is_landlord or is_tenant):
            return request.redirect('/my/documents')

        return http.request.make_response(
            document.document_file,
            headers={
                'Content-Disposition': f'attachment; filename="{document.document_filename}"',
                'Content-Type': 'application/octet-stream',
            }
        )

    @http.route('/my/messages', type='http', auth='user', website=True)
    def portal_my_messages(self, **kw):
        user = request.env.user
        partner = user.partner_id
        
        tickets = request.env['soya.portal.ticket'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc')

        values = {
            'tickets': tickets,
            'page_title': 'Mes Messages',
        }
        return request.render('soya_estate.portal_my_messages', values)

    @http.route('/my/messages/<model("soya.portal.ticket"):ticket>', type='http', auth='user', website=True)
    def portal_message_details(self, ticket, **kw):
        user = request.env.user
        partner = user.partner_id
        
        if ticket.partner_id.id != partner.id:
            return request.redirect('/my/messages')

        values = {
            'ticket': ticket,
            'page_title': ticket.subject,
        }
        return request.render('soya_estate.portal_message_details', values)

    @http.route('/my/messages/<model("soya.portal.ticket"):ticket>/reply', type='http', auth='user', website=True, methods=['POST'])
    def portal_message_reply(self, ticket, **post):
        user = request.env.user
        partner = user.partner_id
        
        if ticket.partner_id.id != partner.id:
            return request.redirect('/my/messages')

        message_text = post.get('message', '')
        
        if message_text:
            ticket.message_post(body=message_text, message_type='comment')

        return request.redirect(f'/my/messages/{ticket.id}')

    @http.route('/my/messages/new', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_new_message(self, **post):
        user = request.env.user
        partner = user.partner_id

        if request.httprequest.method == 'POST':
            subject = post.get('subject', '')
            message = post.get('message', '')

            if subject and message:
                ticket = request.env['soya.portal.ticket'].create({
                    'partner_id': partner.id,
                    'subject': subject,
                    'description': message,
                    'state': 'open',
                })
                return request.redirect(f'/my/messages/{ticket.id}')

        values = {
            'page_title': 'Nouveau Message',
        }
        return request.render('soya_estate.portal_new_message', values)
