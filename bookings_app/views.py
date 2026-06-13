from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rooms.permissions import IsAdmin, IsTenant, IsAdminOrTenant
from rooms.models import Room
from .models import Booking, TenantAssignment, ChatChannel, ChatMessage, TenancyAgreement
from . import serializers



class BookingsView(APIView):
    """
    Admin-only booking management.
    GET: retrieve all bookings.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Booking.objects.select_related('room', 'user').all()
        data = []
        for b in qs:
            data.append({
                'id': b.id,
                'userId': b.user.id if b.user else None,
                'username': b.user.username if b.user else 'Guest',
                'roomId': str(b.room.id),
                'checkIn': b.check_in.isoformat(),
                'checkOut': b.check_out.isoformat(),
                'guests': b.guests,
                'totalPrice': float(b.total_price),
                'status': b.status,
                'guestInfo': b.guest_info,
                'createdAt': b.created_at.isoformat(),
                'updatedAt': b.updated_at.isoformat(),
                'room': {
                    'id': str(b.room.id),
                    'name': b.room.name,
                    'location': b.room.location,
                }
            })
        return Response({'success': True, 'data': data})


class UpdateBookingStatusView(APIView):
    """Admin-only booking status update."""
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        status_val = request.data.get('status')
        if status_val not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return Response({'success': False, 'error': 'Invalid status', 'status': 422}, status=422)

        try:
            b = Booking.objects.get(id=pk)
        except Booking.DoesNotExist:
            return Response({'success': False, 'error': 'Booking not found', 'status': 404}, status=404)

        b.status = status_val
        b.save(update_fields=['status', 'updated_at'])
        return Response({'success': True, 'data': {'id': b.id, 'status': b.status, 'updatedAt': b.updated_at.isoformat()}})


class RentScheduleView(APIView):
    """Admin-only rent schedule management."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from .models import RentSchedule
        schedules = RentSchedule.objects.all().prefetch_related('payment_history')
        serializer = serializers.RentScheduleSerializer(schedules, many=True)
        return Response({'success': True, 'data': serializer.data})

    def post(self, request):
        from .models import RentSchedule
        serializer = serializers.RentScheduleCreateSerializer(data=request.data)
        if serializer.is_valid():
            schedule = serializer.save()
            return Response({'success': True, 'data': serializers.RentScheduleSerializer(schedule).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class RentScheduleDetailView(APIView):
    """Admin-only rent schedule detail, update, delete."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        from .models import RentSchedule
        try:
            schedule = RentSchedule.objects.prefetch_related('payment_history').get(pk=pk)
            return Response({'success': True, 'data': serializers.RentScheduleSerializer(schedule).data})
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)

    def put(self, request, pk):
        from .models import RentSchedule
        try:
            schedule = RentSchedule.objects.get(pk=pk)
            serializer = serializers.RentScheduleSerializer(schedule, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'data': serializer.data})
            return Response({'success': False, 'error': serializer.errors}, status=400)
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)

    def delete(self, request, pk):
        from .models import RentSchedule
        try:
            schedule = RentSchedule.objects.get(pk=pk)
            schedule.delete()
            return Response({'success': True, 'message': 'Schedule deleted'})
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)


class RentPaymentView(APIView):
    """Admin-only rent payment recording."""
    permission_classes = [IsAdmin]

    def post(self, request, schedule_id):
        from .models import RentSchedule, RentPayment
        try:
            schedule = RentSchedule.objects.get(pk=schedule_id)
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)

        serializer = serializers.RentPaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(schedule=schedule)
            return Response({'success': True, 'data': serializers.RentPaymentSerializer(payment).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class RentReminderView(APIView):
    """Admin-only rent due reminders."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from .models import RentSchedule
        today = timezone.now().date()
        reminders = []

        schedules = RentSchedule.objects.all().prefetch_related('payment_history')
        for schedule in schedules:
            if schedule.status != 'active':
                continue

            last_day = (timezone.datetime(today.year, today.month, 28) + timezone.timedelta(days=4)).replace(day=1) - timezone.timedelta(days=1)
            safe_due_day = min(schedule.due_day, last_day.day)
            due_date = timezone.datetime(today.year, today.month, safe_due_day).date()
            days_until_due = (due_date - today).days

            if days_until_due <= 5 and days_until_due >= -30:
                current_month = today.strftime('%Y-%m')
                payment_exists = any(
                    p.due_date.strftime('%Y-%m') == current_month and p.status == 'paid'
                    for p in schedule.payment_history.all()
                )
                if not payment_exists:
                    reminders.append({
                        'id': f"rent-{schedule.id}-{current_month}",
                        'scheduleId': schedule.id,
                        'roomName': schedule.room_name,
                        'tenantName': schedule.tenant_name,
                        'dueDate': due_date.isoformat(),
                        'amount': float(schedule.monthly_rent),
                        'dismissed': False,
                    })

        return Response({'success': True, 'data': reminders})


# ─── Tenant Assignment Views ──────────────────────────────────────────────────


class TenantAssignmentListView(APIView):
    """Admin: list and create tenant-room assignments."""
    permission_classes = [IsAdmin]

    def get(self, request):
        status_filter = request.query_params.get('status')
        qs = TenantAssignment.objects.select_related('tenant', 'room').all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        serializer = serializers.TenantAssignmentSerializer(qs, many=True)
        return Response({'success': True, 'data': serializer.data})

    def post(self, request):
        serializer = serializers.TenantAssignmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            assignment = serializer.save()
            # Auto-promote user to tenant role if they're still a customer
            try:
                from accounts.models import Client
                client, _ = Client.objects.get_or_create(
                    user=assignment.tenant,
                    defaults={'mobile_no': '', 'role': 'tenant', 'image': ''}
                )
                if client.role == 'customer':
                    client.role = 'tenant'
                    client.save(update_fields=['role'])
            except Exception:
                pass

            return Response({
                'success': True,
                'data': serializers.TenantAssignmentSerializer(assignment).data
            }, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class TenantAssignmentDetailView(APIView):
    """Admin: update and delete tenant assignments."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            assignment = TenantAssignment.objects.select_related('tenant', 'room').get(pk=pk)
            return Response({'success': True, 'data': serializers.TenantAssignmentSerializer(assignment).data})
        except TenantAssignment.DoesNotExist:
            return Response({'success': False, 'error': 'Assignment not found'}, status=404)

    def put(self, request, pk):
        try:
            assignment = TenantAssignment.objects.get(pk=pk)
            serializer = serializers.TenantAssignmentSerializer(assignment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'data': serializer.data})
            return Response({'success': False, 'error': serializer.errors}, status=400)
        except TenantAssignment.DoesNotExist:
            return Response({'success': False, 'error': 'Assignment not found'}, status=404)

    def delete(self, request, pk):
        try:
            assignment = TenantAssignment.objects.get(pk=pk)
            assignment.delete()
            return Response({'success': True, 'message': 'Assignment deleted'})
        except TenantAssignment.DoesNotExist:
            return Response({'success': False, 'error': 'Assignment not found'}, status=404)


class MyAssignmentView(APIView):
    """Tenant: view own assignment (property, room, rent details)."""
    permission_classes = [IsAdminOrTenant]

    def get(self, request):
        assignments = TenantAssignment.objects.select_related('tenant', 'room').filter(
            tenant=request.user,
            status='active'
        )
        if not assignments.exists():
            return Response({'success': True, 'data': None, 'message': 'No active assignment found'})

        serializer = serializers.TenantAssignmentSerializer(assignments.first())
        # Also include room details
        assignment = assignments.first()
        from rooms.serializers import RoomSerializer
        room_data = RoomSerializer(assignment.room).data

        return Response({
            'success': True,
            'data': {
                'assignment': serializer.data,
                'room': room_data,
            }
        })


# ─── Tenant Rent Views ────────────────────────────────────────────────────────


class MyRentSchedulesView(APIView):
    """Tenant: view own rent schedules."""
    permission_classes = [IsAdminOrTenant]

    def get(self, request):
        from .models import RentSchedule
        # Find schedules linked to this user directly, or by matching tenant name/email
        schedules = RentSchedule.objects.filter(
            tenant_user=request.user
        ).prefetch_related('payment_history')

        # Fallback: also match by email if no direct FK link
        if not schedules.exists():
            schedules = RentSchedule.objects.filter(
                tenant_email=request.user.email
            ).prefetch_related('payment_history')

        serializer = serializers.RentScheduleSerializer(schedules, many=True)
        return Response({'success': True, 'data': serializer.data})


class MyRentRemindersView(APIView):
    """Tenant: view own upcoming rent reminders."""
    permission_classes = [IsAdminOrTenant]

    def get(self, request):
        from .models import RentSchedule
        today = timezone.now().date()
        reminders = []

        # Get schedules for this tenant
        schedules = RentSchedule.objects.filter(
            tenant_user=request.user
        ).prefetch_related('payment_history')

        if not schedules.exists():
            schedules = RentSchedule.objects.filter(
                tenant_email=request.user.email
            ).prefetch_related('payment_history')

        for schedule in schedules:
            if schedule.status != 'active':
                continue

            last_day = (timezone.datetime(today.year, today.month, 28) + timezone.timedelta(days=4)).replace(day=1) - timezone.timedelta(days=1)
            safe_due_day = min(schedule.due_day, last_day.day)
            due_date = timezone.datetime(today.year, today.month, safe_due_day).date()
            days_until_due = (due_date - today).days

            if days_until_due <= 14 and days_until_due >= -30:
                current_month = today.strftime('%Y-%m')
                payment_exists = any(
                    p.due_date.strftime('%Y-%m') == current_month and p.status == 'paid'
                    for p in schedule.payment_history.all()
                )
                if not payment_exists:
                    reminders.append({
                        'id': f"rent-{schedule.id}-{current_month}",
                        'scheduleId': schedule.id,
                        'roomName': schedule.room_name,
                        'dueDate': due_date.isoformat(),
                        'amount': float(schedule.monthly_rent),
                        'daysUntilDue': days_until_due,
                        'isOverdue': days_until_due < 0,
                    })

        return Response({'success': True, 'data': reminders})


# ─── Chat Channels & Messages API ───────────────────────────────────────────

class ChatChannelView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        
        if role == 'admin' or user.is_staff:
            channels = ChatChannel.objects.select_related('tenant', 'admin').all().prefetch_related('messages')
            serializer = serializers.ChatChannelSerializer(channels, many=True)
            return Response({'success': True, 'data': serializer.data})
        else:
            # Tenant
            # Find active assignment to know the property name
            assignment = TenantAssignment.objects.filter(tenant=user, status='active').first()
            prop_name = assignment.property_name if assignment else "General Inquiry"
            
            # Get or create channel for this tenant
            channel, created = ChatChannel.objects.get_or_create(
                tenant=user,
                defaults={'property_name': prop_name}
            )
            # Update property name if it changed/was initialized
            if not created and assignment and channel.property_name != assignment.property_name:
                channel.property_name = assignment.property_name
                channel.save()
                
            serializer = serializers.ChatChannelSerializer(channel)
            return Response({'success': True, 'data': serializer.data})

    def post(self, request):
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        
        if role == 'admin' or user.is_staff:
            tenant_id = request.data.get('tenant_id')
            property_name = request.data.get('property_name')
            
            if not tenant_id or not property_name:
                return Response({'success': False, 'error': 'tenant_id and property_name are required'}, status=400)
                
            from django.contrib.auth.models import User
            try:
                tenant_user = User.objects.get(id=tenant_id)
            except User.DoesNotExist:
                return Response({'success': False, 'error': 'Tenant user not found'}, status=404)
                
            channel, created = ChatChannel.objects.get_or_create(
                tenant=tenant_user,
                defaults={'property_name': property_name, 'admin': user}
            )
            serializer = serializers.ChatChannelSerializer(channel)
            return Response({'success': True, 'data': serializer.data}, status=201 if created else 200)
        else:
            return Response({'success': False, 'error': 'Permission denied'}, status=403)



class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, channel_id):
        try:
            channel = ChatChannel.objects.get(id=channel_id)
        except ChatChannel.DoesNotExist:
            return Response({'success': False, 'error': 'Channel not found'}, status=404)
        
        # Verify permissions: only admin or the channel's tenant can read
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        if role != 'admin' and not user.is_staff and channel.tenant != user:
            return Response({'success': False, 'error': 'Permission denied'}, status=403)
            
        messages = channel.messages.all().order_by('created_at')
        serializer = serializers.ChatMessageSerializer(messages, many=True)
        return Response({'success': True, 'data': serializer.data})

    def post(self, request, channel_id):
        try:
            channel = ChatChannel.objects.get(id=channel_id)
        except ChatChannel.DoesNotExist:
            return Response({'success': False, 'error': 'Channel not found'}, status=404)
            
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        if role != 'admin' and not user.is_staff and channel.tenant != user:
            return Response({'success': False, 'error': 'Permission denied'}, status=403)
            
        serializer = serializers.ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            msg = serializer.save(channel=channel, sender=user)
            
            # Extract text if file uploaded
            if msg.file_url:
                try:
                    from bookings_app.services.document_extractor import extract_text_from_url
                    msg.extracted_text = extract_text_from_url(msg.file_url, msg.file_name)
                    msg.save(update_fields=['extracted_text'])
                except Exception as e:
                    # Log but don't fail message creation
                    print(f"Extraction failed: {str(e)}")
                    
            return Response({'success': True, 'data': serializers.ChatMessageSerializer(msg).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


# ─── AI Tenancy Agreement Draft Generator ─────────────────────────────────────

class GenerateAgreementView(APIView):
    permission_classes = [IsAdmin] # Only admins generate drafts

    def post(self, request):
        channel_id = request.data.get('channel_id')
        if not channel_id:
            return Response({'success': False, 'error': 'channel_id is required'}, status=400)
            
        try:
            channel = ChatChannel.objects.get(id=channel_id)
        except ChatChannel.DoesNotExist:
            return Response({'success': False, 'error': 'Channel not found'}, status=404)
            
        # Get active assignment for the tenant to gather baseline contract info
        tenant = channel.tenant
        assignment = TenantAssignment.objects.filter(tenant=tenant, status='active').first()
        
        # Build context from assignment
        details_context = f"Tenant Username: {tenant.username}\nTenant Email: {tenant.email}\n"
        if assignment:
            details_context += f"Property Name: {assignment.property_name}\n"
            details_context += f"Room: {assignment.room.name if assignment.room else 'N/A'}\n"
            details_context += f"Monthly Rent: ${assignment.monthly_rent}\n"
            details_context += f"Security Deposit: ${assignment.deposit}\n"
            details_context += f"Start Date: {assignment.start_date}\n"
            if assignment.end_date:
                details_context += f"End Date: {assignment.end_date}\n"
        else:
            details_context += f"Property Name: {channel.property_name}\n"
            
        # Compile Chat History
        chat_messages = channel.messages.all().order_by('created_at')
        chat_log = ""
        extracted_documents_content = ""
        
        for msg in chat_messages:
            sender_label = "Admin" if msg.sender.is_staff or (hasattr(msg.sender, 'client') and msg.sender.client.role == 'admin') else "Tenant"
            chat_log += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {sender_label} ({msg.sender.username}): {msg.content}\n"
            
            if msg.file_url and msg.extracted_text:
                extracted_documents_content += f"--- Document Shared: {msg.file_name or 'unnamed'} ---\n{msg.extracted_text}\n\n"
                
        # Call Groq API
        from openai import OpenAI
        from django.conf import settings
        
        api_key = getattr(settings, 'NEOSCAPE_API_KEY', '')
        if not api_key:
            return Response({'success': False, 'error': 'Groq/NeoScape API Key is not configured on the backend settings.'}, status=500)
            
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            
            SYSTEM_PROMPT = """You are a professional real estate legal assistant. 
Your job is to generate a comprehensive Tenancy Agreement in Markdown format.
Use the provided Chat History (negotiations), System Records (assignment details), and Extracted Terms/Inventory Files.
Ensure you cover:
1. Names of parties (Landlord/Tenant).
2. Property Address and Room details.
3. Rental terms (amount, due date, deposit).
4. Rules, terms and conditions.
5. Inventory list of items and their condition (based on the chat and uploaded files).
Return only the Markdown agreement ready to sign. Do not include introductory notes, chat banter, or explanation. Begin directly with the contract title (e.g. # RESIDENTIAL TENANCY AGREEMENT)."""

            USER_PROMPT = f"""System Records (Baseline Details):
{details_context}

Chat History:
{chat_log}

Extracted Document Texts (shared terms/inventories):
{extracted_documents_content}
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT}
                ],
                temperature=0.2,
            )
            
            agreement_text = response.choices[0].message.content
            
            # Create or update draft agreement in database
            agreement, created = TenancyAgreement.objects.get_or_create(
                channel=channel,
                defaults={
                    'property_name': channel.property_name,
                    'tenant': tenant,
                    'room_id': assignment.room.id if assignment and assignment.room else None,
                    'agreement_text': agreement_text,
                    'status': 'draft'
                }
            )
            if not created:
                agreement.agreement_text = agreement_text
                # Reset signatures since we regenerated the draft
                agreement.tenant_signed = False
                agreement.tenant_signature_svg = None
                agreement.tenant_signed_at = None
                agreement.admin_signed = False
                agreement.admin_signature_svg = None
                agreement.admin_signed_at = None
                agreement.status = 'draft'
                agreement.save()
                
            return Response({
                'success': True,
                'data': serializers.TenancyAgreementSerializer(agreement).data
            })
            
        except Exception as e:
            return Response({'success': False, 'error': f"AI Agreement generation failed: {str(e)}"}, status=500)


# ─── Tenancy Agreement Signatures & Review API ─────────────────────────────────

class TenancyAgreementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        channel_id = request.query_params.get('channel_id')
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        
        if channel_id:
            try:
                channel = ChatChannel.objects.get(id=channel_id)
            except ChatChannel.DoesNotExist:
                return Response({'success': False, 'error': 'Channel not found'}, status=404)
                
            if role != 'admin' and not user.is_staff and channel.tenant != user:
                return Response({'success': False, 'error': 'Permission denied'}, status=403)
                
            agreements = TenancyAgreement.objects.filter(channel=channel)
        else:
            if role == 'admin' or user.is_staff:
                agreements = TenancyAgreement.objects.all()
            else:
                agreements = TenancyAgreement.objects.filter(tenant=user)
                
        serializer = serializers.TenancyAgreementSerializer(agreements, many=True)
        return Response({'success': True, 'data': serializer.data})


class TenancyAgreementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return TenancyAgreement.objects.get(pk=pk)
        except TenancyAgreement.DoesNotExist:
            return None

    def get(self, request, pk):
        agreement = self.get_object(pk)
        if not agreement:
            return Response({'success': False, 'error': 'Agreement not found'}, status=404)
            
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        if role != 'admin' and not user.is_staff and agreement.tenant != user:
            return Response({'success': False, 'error': 'Permission denied'}, status=403)
            
        return Response({'success': True, 'data': serializers.TenancyAgreementSerializer(agreement).data})

    def patch(self, request, pk):
        agreement = self.get_object(pk)
        if not agreement:
            return Response({'success': False, 'error': 'Agreement not found'}, status=404)
            
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        
        status_val = request.data.get('status')
        text_val = request.data.get('agreement_text')
        
        if status_val == 'rejected':
            agreement.status = 'rejected'
            agreement.save(update_fields=['status'])
            return Response({'success': True, 'data': serializers.TenancyAgreementSerializer(agreement).data})
            
        if role == 'admin' or user.is_staff:
            if text_val:
                agreement.agreement_text = text_val
            if status_val:
                agreement.status = status_val
            agreement.save()
            return Response({'success': True, 'data': serializers.TenancyAgreementSerializer(agreement).data})
        else:
            return Response({'success': False, 'error': 'Permission denied'}, status=403)


class SignAgreementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            agreement = TenancyAgreement.objects.get(pk=pk)
        except TenancyAgreement.DoesNotExist:
            return Response({'success': False, 'error': 'Agreement not found'}, status=404)
            
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'
        
        signature_svg = request.data.get('signature_svg')
        if not signature_svg:
            return Response({'success': False, 'error': 'signature_svg is required'}, status=400)
            
        if role == 'admin' or user.is_staff:
            agreement.admin_signed = True
            agreement.admin_signature_svg = signature_svg
            agreement.admin_signed_at = timezone.now()
        elif agreement.tenant == user:
            agreement.tenant_signed = True
            agreement.tenant_signature_svg = signature_svg
            agreement.tenant_signed_at = timezone.now()
        else:
            return Response({'success': False, 'error': 'You are not authorized to sign this agreement.'}, status=403)
            
        if agreement.tenant_signed and agreement.admin_signed:
            agreement.status = 'signed'
            
        agreement.save()
        return Response({
            'success': True,
            'data': serializers.TenancyAgreementSerializer(agreement).data
        })

