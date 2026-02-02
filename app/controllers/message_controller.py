from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.models import User, db
from app.models.message import Message
from datetime import datetime

message_bp = Blueprint('message', __name__)

@message_bp.route('/')
@message_bp.route('/messages')
@login_required
def index():
    """Display the messaging dashboard"""
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('messages/index.html', users=users, datetime=datetime)

@message_bp.route('/messages/<int:user_id>')
@login_required
def conversation(user_id):
    """Display conversation with a specific user"""
    recipient = User.query.get_or_404(user_id)
    
    # Get messages between current user and recipient
    sent_messages = Message.query.filter_by(
        sender_id=current_user.id, recipient_id=user_id
    ).all()
    
    received_messages = Message.query.filter_by(
        sender_id=user_id, recipient_id=current_user.id
    ).all()
    
    # Combine and sort messages by timestamp
    messages = sorted(sent_messages + received_messages, key=lambda x: x.timestamp)
    
    # Mark received messages as read
    for message in received_messages:
        if not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('messages/conversation.html', messages=messages, recipient=recipient, users=users, datetime=datetime)

@message_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a new message"""
    recipient_id = request.form.get('recipient_id')
    content = request.form.get('content')
    
    if not recipient_id or not content:
        flash('Message could not be sent. Please try again.', 'danger')
        return redirect(url_for('message.index'))
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content,
        timestamp=datetime.now(),
        is_read=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    return redirect(url_for('message.conversation', user_id=recipient_id))

@message_bp.route('/messages/unread')
@login_required
def unread_count():
    """Get count of unread messages for the current user"""
    count = Message.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).count()
    
    return jsonify({'count': count})