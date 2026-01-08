from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Any, cast
from datetime import datetime, timezone, timedelta
from typing import Sequence
from collections import defaultdict
from .database import get_session
from .models import User, DoctorProfile, Slot, Appointment
from .crud import create_user

router = APIRouter(tags=["frontend"])

# HTML Templates will be inline for simplicity
def get_home_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Doctor Appointment System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 400px;
                width: 100%;
            }
            h1 { color: #667eea; margin-bottom: 10px; text-align: center; }
            h2 { color: #333; margin-bottom: 20px; font-size: 20px; text-align: center; }
            .btn-group { display: flex; gap: 15px; margin-bottom: 30px; }
            .tab-btn {
                flex: 1;
                padding: 12px;
                border: 2px solid #667eea;
                background: white;
                color: #667eea;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s;
            }
            .tab-btn:hover { background: #f0f0f0; }
            .tab-btn.active {
                background: #667eea;
                color: white;
            }
            .form-group { margin-bottom: 20px; }
            label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 600;
            }
            input, select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            .submit-btn {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .submit-btn:hover { transform: translateY(-2px); }
            .submit-btn:active { transform: translateY(0); }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .message {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
            .error { background: #fee; color: #c33; border: 1px solid #fcc; }
            .success { background: #efe; color: #3c3; border: 1px solid #cfc; }
            .specialty-note {
                font-size: 12px;
                color: #888;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Doctor Appointment</h1>
            <h2>Welcome! Please sign up or login</h2>
            
            <div class="btn-group">
                <button class="tab-btn active" onclick="showTab('patient')">Patient</button>
                <button class="tab-btn" onclick="showTab('doctor')">Doctor</button>
            </div>

            <!-- Patient Tab -->
            <div id="patient-tab" class="tab-content active">
                <h3 style="margin-bottom: 20px; color: #667eea;">Patient Registration</h3>
                <form action="/register-patient" method="POST">
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="full_name" required placeholder="Enter your full name">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" required placeholder="your.email@example.com">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required placeholder="Create a password">
                    </div>
                    <button type="submit" class="submit-btn">Register as Patient</button>
                </form>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">
                
                <h3 style="margin-bottom: 20px; color: #667eea;">Already have an account?</h3>
                <form action="/login" method="POST">
                    <input type="hidden" name="role" value="patient">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" required placeholder="your.email@example.com">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required placeholder="Enter your password">
                    </div>
                    <button type="submit" class="submit-btn" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">Login as Patient</button>
                </form>
            </div>

            <!-- Doctor Tab -->
            <div id="doctor-tab" class="tab-content">
                <h3 style="margin-bottom: 20px; color: #667eea;">Doctor Registration</h3>
                <form action="/register-doctor" method="POST">
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="full_name" required placeholder="Dr. Your Name">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" required placeholder="doctor@hospital.com">
                    </div>
                    <div class="form-group">
                        <label>Specialization</label>
                        <select name="specialization" required>
                            <option value="">Select Specialization</option>
                            <option value="Cardiology">Cardiology</option>
                            <option value="Dermatology">Dermatology</option>
                            <option value="Pediatrics">Pediatrics</option>
                            <option value="Orthopedics">Orthopedics</option>
                            <option value="General Medicine">General Medicine</option>
                            <option value="Neurology">Neurology</option>
                            <option value="Psychiatry">Psychiatry</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required placeholder="Create a password">
                    </div>
                    <button type="submit" class="submit-btn">Register as Doctor</button>
                </form>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">
                
                <h3 style="margin-bottom: 20px; color: #667eea;">Already have an account?</h3>
                <form action="/login" method="POST">
                    <input type="hidden" name="role" value="doctor">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" required placeholder="doctor@hospital.com">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required placeholder="Enter your password">
                    </div>
                    <button type="submit" class="submit-btn" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">Login as Doctor</button>
                </form>
            </div>
        </div>

        <script>
            function showTab(tab) {
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                
                if (tab === 'patient') {
                    document.getElementById('patient-tab').classList.add('active');
                    document.querySelector('.tab-btn:first-child').classList.add('active');
                } else {
                    document.getElementById('doctor-tab').classList.add('active');
                    document.querySelector('.tab-btn:last-child').classList.add('active');
                }
            }
        </script>
    </body>
    </html>
    """

def get_patient_dashboard(doctors: Sequence[DoctorProfile], appointments: Sequence[Appointment], user_name: str) -> str:
    doctors_html = ""
    for doc in doctors:
        doctors_html += f"""
        <div class="doctor-card">
            <h3>Dr. {doc.user.full_name if doc.user else ''}</h3>
            <p class="specialty">{doc.specialization}</p>
            <a href="/book-appointment/{doc.id}" class="book-btn">View Available Slots</a>
        </div>
        """
    
    appointments_html = ""
    current_time = datetime.now(timezone.utc)
    
    for apt in appointments:
        # Check if appointment can be cancelled (more than 10 hours away)
        can_cancel = False
        time_until = ""
        if apt.slot and apt.slot.start_time:
            # Make slot time timezone-aware if it isn't
            slot_time = apt.slot.start_time
            if slot_time.tzinfo is None:
                slot_time = slot_time.replace(tzinfo=timezone.utc)
            
            time_diff = slot_time - current_time
            hours_until = time_diff.total_seconds() / 3600
            can_cancel = hours_until > 10
            
            if can_cancel:
                time_until = f"<span style='color: #4caf50; font-size: 0.9em;'>✓ Can cancel (>{int(hours_until)}h away)</span>"
            else:
                time_until = f"<span style='color: #f44336; font-size: 0.9em;'>✗ Cannot cancel (<10h away)</span>"
        
        cancel_button = ""
        if can_cancel and apt.id:
            cancel_button = f"""
            <form action="/cancel-appointment/{apt.id}" method="POST" style="display: inline;" 
                  onsubmit="return confirm('Are you sure you want to cancel this appointment?');">
                <button type="submit" style="background: #f44336; color: white; padding: 8px 16px; 
                        border: none; border-radius: 5px; cursor: pointer; font-weight: 600; margin-top: 10px;">
                    Cancel Appointment
                </button>
            </form>
            """
        
        appointments_html += f"""
        <div class="appointment-card">
            <h4>Dr. {apt.doctor.user.full_name if (apt.doctor and apt.doctor.user) else ''}</h4>
            <p><strong>Specialization:</strong> {apt.doctor.specialization if apt.doctor else ''}</p>
            <p><strong>Time:</strong> {apt.slot.start_time.strftime('%B %d, %Y at %I:%M %p') if apt.slot else 'TBD'}</p>
            <p><strong>Reason:</strong> {apt.reason or 'General checkup'}</p>
            <p>{time_until}</p>
            {cancel_button}
        </div>
        """
    
    if not appointments_html:
        appointments_html = "<p style='text-align: center; color: #888;'>No appointments yet. Book one below!</p>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Patient Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .header h1 {{ font-size: 32px; }}
            .logout-btn {{
                background: white;
                color: #667eea;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
            }}
            .section {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #667eea;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .doctor-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
            }}
            .doctor-card {{
                border: 2px solid #e0e0e0;
                padding: 20px;
                border-radius: 12px;
                transition: all 0.3s;
            }}
            .doctor-card:hover {{
                border-color: #667eea;
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
                transform: translateY(-5px);
            }}
            .doctor-card h3 {{
                color: #333;
                margin-bottom: 10px;
            }}
            .specialty {{
                color: #667eea;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .book-btn {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: transform 0.2s;
            }}
            .book-btn:hover {{ transform: translateY(-2px); }}
            .appointment-card {{
                border-left: 4px solid #667eea;
                padding: 15px;
                background: #f9f9f9;
                margin-bottom: 15px;
                border-radius: 8px;
            }}
            .appointment-card h4 {{
                color: #667eea;
                margin-bottom: 10px;
            }}
            .appointment-card p {{
                color: #555;
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Welcome, {user_name}! 👋</h1>
                <p style="margin-top: 10px; opacity: 0.9;">Book appointments with our top doctors</p>
            </div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>

        <div class="section">
            <h2>📅 Your Appointments</h2>
            {appointments_html}
        </div>

        <div class="section">
            <h2>👨‍⚕️ Available Doctors</h2>
            <div class="doctor-grid">
                {doctors_html}
            </div>
        </div>
    </body>
    </html>
    """

def get_booking_page(doctor: DoctorProfile, slots: Sequence[Slot]) -> str:
    # Group slots by date
    slots_by_date: dict[str, list[Slot]] = defaultdict(list)
    available_count = 0
    
    for slot in slots:
        date_key = slot.start_time.strftime('%Y-%m-%d')
        slots_by_date[date_key].append(slot)
        if not slot.is_booked:
            available_count += 1
    
    if not slots_by_date:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Book Appointment - No Slots</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f5f7fa;
                    padding: 20px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="color: #667eea; margin-bottom: 20px;">Dr. {doctor.user.full_name if doctor.user else ''}</h1>
                <p style="color: #888; padding: 40px;">⚠️ No available slots at the moment. Please check back later.</p>
                <a href="/patient-dashboard" style="display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px;">Back to Dashboard</a>
            </div>
        </body>
        </html>
        """
    
    date_sections = ""
    for date_key in sorted(slots_by_date.keys()):
        date_slots = sorted(slots_by_date[date_key], key=lambda s: s.start_time)
        date_display = date_slots[0].start_time.strftime('%B %d, %Y')
        
        slots_dropdown = "<option value=''>-- Select Time Slot --</option>"
        for slot in date_slots:
            if slot.id is None:
                continue
            time_display = f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p') if slot.end_time else 'TBD'}"
            if slot.is_booked:
                slots_dropdown += f"<option value='{slot.id}' disabled style='color: #999; background: #f0f0f0;'>{time_display} (Booked)</option>"
            else:
                slots_dropdown += f"<option value='{slot.id}'>{time_display}</option>"
        
        date_sections += f"""
        <div class="date-section">
            <h3 style="color: #667eea; margin-bottom: 15px;">📅 {date_display}</h3>
            <form action="/confirm-booking-dropdown" method="POST" class="booking-form">
                <div class="form-group">
                    <label for="slot_{date_key}">Select Time Slot:</label>
                    <select id="slot_{date_key}" name="slot_id" required>
                        {slots_dropdown}
                    </select>
                </div>
                <div class="form-group">
                    <label for="reason_{date_key}">Reason for Visit (Optional):</label>
                    <input type="text" id="reason_{date_key}" name="reason" placeholder="e.g., General checkup, Follow-up visit">
                </div>
                <button type="submit" class="book-btn">Book Selected Slot</button>
            </form>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Appointment</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #667eea;
                margin-bottom: 10px;
            }}
            .doctor-info {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
            }}
            .doctor-info h2 {{ margin-bottom: 5px; }}
            .slot-card {{
                border: 2px solid #e0e0e0;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s;
            }}
            .slot-card:hover {{
                border-color: #667eea;
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
            }}
            .time {{
                font-size: 16px;
                color: #333;
                font-weight: 600;
            }}
            .book-slot-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }}
            .book-slot-btn:hover {{ transform: translateY(-2px); }}
            .back-btn {{
                display: inline-block;
                margin-top: 20px;
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }}
            .back-btn:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Book an Appointment</h1>
            
            <div class="doctor-info">
                <h2>Dr. {doctor.user.full_name if doctor.user else ''}</h2>
                <p style="opacity: 0.9; margin-top: 5px;">{doctor.specialization}</p>
            </div>

            <div class="info-banner">
                ✨ {available_count} Available Slot{'s' if available_count != 1 else ''} • Booked slots shown as disabled
            </div>

            {date_sections}

            <a href="/patient-dashboard" class="back-btn">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

def get_doctor_dashboard(
    doctor: DoctorProfile,
    slots: Sequence[Slot],
    appointments: Sequence[Appointment],
    user_name: str,
) -> str:
    slots_html = ""
    available_slots = 0
    booked_slots = 0
    
    for slot in slots:
        if slot.is_booked:
            booked_slots += 1
            status_badge = "<span class='status booked'>🔴 Booked</span>"
        else:
            available_slots += 1
            status_badge = "<span class='status available'>🟢 Available</span>"
        
        duration = ""
        if slot.end_time:
            duration_minutes = int((slot.end_time - slot.start_time).total_seconds() / 60)
            duration = f" ({duration_minutes} min)"
            
        slots_html += f"""
        <div class="slot-item">
            <span>{slot.start_time.strftime('%B %d, %Y at %I:%M %p')}{duration}</span>
            {status_badge}
        </div>
        """
    
    if not slots_html:
        slots_html = "<p style='text-align: center; color: #888;'>No slots created yet.</p>"
    else:
        slots_html = f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #4caf50, #45a049); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{available_slots}</div>
                <div>Available Slots</div>
            </div>
            <div style="background: linear-gradient(135deg, #f44336, #e53935); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{booked_slots}</div>
                <div>Booked Slots</div>
            </div>
        </div>
        """ + slots_html

    # Build a unique patient list from appointments
    patients_seen: set[int] = set()
    patients_html = ""
    for apt in appointments:
        if not apt.patient or apt.patient.id is None:
            continue
        if apt.patient.id in patients_seen:
            continue
        patients_seen.add(apt.patient.id)
        patients_html += f"""
        <div class="appointment-card">
            <h4>{apt.patient.full_name or ''}</h4>
            <p><strong>Contact:</strong> {apt.patient.email}</p>
        </div>
        """

    if not patients_html:
        patients_html = "<p style='text-align: center; color: #888;'>No patients yet.</p>"
    
    appointments_html = ""
    for apt in appointments:
        appointments_html += f"""
        <div class="appointment-card">
            <h4>{apt.patient.full_name if apt.patient else ''}</h4>
            <p><strong>Time:</strong> {apt.slot.start_time.strftime('%B %d, %Y at %I:%M %p') if apt.slot else 'TBD'}</p>
            <p><strong>Reason:</strong> {apt.reason or 'General checkup'}</p>
            <p><strong>Contact:</strong> {apt.patient.email if apt.patient else ''}</p>
        </div>
        """
    
    if not appointments_html:
        appointments_html = "<p style='text-align: center; color: #888;'>No appointments booked yet.</p>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Doctor Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .header h1 {{ font-size: 32px; }}
            .logout-btn {{
                background: white;
                color: #11998e;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
            }}
            .section {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #11998e;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .form-row {{
                display: grid;
                grid-template-columns: 1fr 1fr auto;
                gap: 15px;
                align-items: end;
            }}
            .form-group {{
                display: flex;
                flex-direction: column;
            }}
            .form-group label {{
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
            }}
            .form-group input {{
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
            }}
            .add-btn {{
                padding: 12px 24px;
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                height: 44px;
            }}
            .add-btn:hover {{ opacity: 0.9; }}
            .slot-item {{
                display: flex;
                justify-content: space-between;
                padding: 15px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-bottom: 10px;
            }}
            .status {{ 
                font-weight: 600; 
                padding: 5px 15px;
                border-radius: 12px;
                font-size: 0.9em;
            }}
            .status.available {{
                background: #4caf50;
                color: white;
            }}
            .status.booked {{
                background: #f44336;
                color: white;
            }}
            .appointment-card {{
                border-left: 4px solid #11998e;
                padding: 15px;
                background: #f9f9f9;
                margin-bottom: 15px;
                border-radius: 8px;
            }}
            .appointment-card h4 {{
                color: #11998e;
                margin-bottom: 10px;
            }}
            .appointment-card p {{
                color: #555;
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Dr. {user_name} 👨‍⚕️</h1>
                <p style="margin-top: 10px; opacity: 0.9;">{doctor.specialization}</p>
            </div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>

        <div class="section">
            <h2>➕ Add Availability Window</h2>
            <p style="color: #666; margin-bottom: 15px;">Enter your availability range (e.g., 10 AM to 3 PM). System will automatically create 20-minute slots.</p>
            <form action="/add-slot" method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label>Start Date & Time</label>
                        <input type="datetime-local" name="start_time" required>
                    </div>
                    <div class="form-group">
                        <label>End Date & Time</label>
                        <input type="datetime-local" name="end_time" required>
                    </div>
                    <button type="submit" class="add-btn">Generate 20-Min Slots</button>
                </div>
            </form>
        </div>

        <div class="section">
            <h2>📅 Your Time Slots</h2>
            {slots_html}
        </div>

        <div class="section">
            <h2>👥 Your Patients</h2>
            {patients_html}
        </div>

        <div class="section">
            <h2>👥 Your Appointments</h2>
            {appointments_html}
        </div>
    </body>
    </html>
    """

@router.get("/", response_class=HTMLResponse)
async def home():
    return get_home_page()

@router.post("/register-patient")
async def register_patient(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    from .auth import get_user_by_email
    if get_user_by_email(session, email):
        return HTMLResponse(get_home_page() + "<script>alert('Email already registered!');</script>")
    
    try:
        user, _ = create_user(session, email, password, full_name, "patient")
    except ValueError as e:
        msg = str(e).replace("'", "\\'")
        return HTMLResponse(get_home_page() + f"<script>alert('{msg}');</script>")
    
    response = RedirectResponse(url="/patient-dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    response.set_cookie(key="user_role", value="patient")
    return response

@router.post("/register-doctor")
async def register_doctor(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    specialization: str = Form(...),
    session: Session = Depends(get_session)
):
    from .auth import get_user_by_email
    if get_user_by_email(session, email):
        return HTMLResponse(get_home_page() + "<script>alert('Email already registered!');</script>")
    
    try:
        user, _ = create_user(session, email, password, full_name, "doctor", specialization)
    except ValueError as e:
        msg = str(e).replace("'", "\\'")
        return HTMLResponse(get_home_page() + f"<script>alert('{msg}');</script>")
    
    response = RedirectResponse(url="/doctor-dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    response.set_cookie(key="user_role", value="doctor")
    return response

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    session: Session = Depends(get_session)
):
    from .auth import authenticate_user, get_user_by_email
    
    # Debug: Check if user exists
    existing_user = get_user_by_email(session, email)
    if not existing_user:
        return HTMLResponse(get_home_page() + "<script>alert('No account found with this email. Please register first.');</script>")
    
    # Debug: Check if role matches
    if existing_user.role != role:
        return HTMLResponse(get_home_page() + f"<script>alert('This email is registered as {existing_user.role}, not {role}. Please select the correct role.');</script>")
    
    # Authenticate user
    user = authenticate_user(session, email, password)
    
    if not user:
        return HTMLResponse(get_home_page() + "<script>alert('Incorrect password. Please try again.');</script>")
    
    redirect_url = "/patient-dashboard" if role == "patient" else "/doctor-dashboard"
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    response.set_cookie(key="user_role", value=role)
    return response

@router.get("/patient-dashboard", response_class=HTMLResponse)
async def patient_dashboard(request: Request, session: Session = Depends(get_session)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    user = session.get(User, int(user_id))
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Get all doctors with their user info
    doctors = session.exec(select(DoctorProfile)).all()
    
    # Get user's appointments
    stmt = select(Appointment).where(Appointment.patient_id == int(user_id))
    appointments = session.exec(stmt).all()
    
    return get_patient_dashboard(doctors, appointments, user.full_name or "")

@router.get("/book-appointment/{doctor_id}", response_class=HTMLResponse)
async def book_appointment_page(doctor_id: int, request: Request, session: Session = Depends(get_session)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    doctor = session.get(DoctorProfile, doctor_id)
    if not doctor:
        return RedirectResponse(url="/patient-dashboard", status_code=303)
    
    # Get ALL slots (both available and booked) to show in dropdown
    stmt = select(Slot).where(Slot.doctor_id == doctor_id)
    slots = session.exec(stmt).all()
    # Sort in Python since order_by with datetime can have issues
    slots = sorted(slots, key=lambda s: s.start_time)
    
    return get_booking_page(doctor, slots)

@router.post("/confirm-booking-dropdown")
async def confirm_booking_dropdown(
    request: Request,
    slot_id: int = Form(...),
    reason: str = Form(""),
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    # Fetch the slot with race condition protection
    slot = session.get(Slot, slot_id)
    if not slot:
        return RedirectResponse(url="/patient-dashboard", status_code=303)
    
    # Check if slot is already booked (race condition protection)
    if slot.is_booked:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Booking Failed</title>
            <style>
                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f5f7fa; }
                .error-box { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center; max-width: 500px; }
                h1 { color: #f44336; margin-bottom: 20px; }
                p { color: #555; margin-bottom: 30px; line-height: 1.6; }
                a { background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block; }
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>⚠️ Booking Failed</h1>
                <p>Sorry, this time slot was just booked by another patient. Please select a different available time slot.</p>
                <a href="/patient-dashboard">Back to Dashboard</a>
            </div>
        </body>
        </html>
        """)
    
    # Create appointment and mark slot as booked
    appointment = Appointment(
        doctor_id=slot.doctor_id,
        patient_id=int(user_id),
        slot_id=slot_id,
        reason=reason or None
    )
    slot.is_booked = True
    
    session.add(appointment)
    session.add(slot)
    session.commit()
    
    return RedirectResponse(url="/patient-dashboard", status_code=303)

@router.post("/confirm-booking/{slot_id}")
async def confirm_booking(
    slot_id: int,
    request: Request,
    reason: str = Form(""),
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    slot = session.get(Slot, slot_id)
    if not slot or slot.is_booked:
        return HTMLResponse("<script>alert('Slot not available!'); window.location='/patient-dashboard';</script>")
    
    appointment = Appointment(
        doctor_id=slot.doctor_id,
        patient_id=int(user_id),
        slot_id=slot_id,
        reason=reason if reason else None
    )
    slot.is_booked = True
    
    session.add(appointment)
    session.add(slot)
    session.commit()
    
    return RedirectResponse(url="/patient-dashboard", status_code=303)

@router.get("/doctor-dashboard", response_class=HTMLResponse)
async def doctor_dashboard(request: Request, session: Session = Depends(get_session)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    if request.cookies.get("user_role") != "doctor":
        return RedirectResponse(url="/", status_code=303)

    user = session.get(User, int(user_id))

    stmt = select(DoctorProfile).where(DoctorProfile.user_id == int(user_id))
    doctor = session.exec(stmt).first()
    if not doctor:
        return RedirectResponse(url="/", status_code=303)

    stmt = select(Slot).where(Slot.doctor_id == doctor.id)
    slots = session.exec(stmt).all()

    stmt = (
        select(Appointment)
        .where(Appointment.doctor_id == doctor.id)
        .options(
            selectinload(cast(Any, Appointment.patient)),
            selectinload(cast(Any, Appointment.slot)),
        )
    )
    appointments = session.exec(stmt).all()

    return get_doctor_dashboard(doctor, slots, appointments, (user.full_name or "") if user else "")

@router.post("/add-slot")
async def add_slot(
    request: Request,
    start_time: str = Form(...),
    end_time: str = Form(...),
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    stmt = select(DoctorProfile).where(DoctorProfile.user_id == int(user_id))
    doctor = session.exec(stmt).first()
    if not doctor:
        return RedirectResponse(url="/", status_code=303)

    if doctor.id is None:
        return RedirectResponse(url="/", status_code=303)

    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)

    # Generate 20-minute slots automatically
    current: datetime = start_dt
    slots_created = 0
    
    while current < end_dt:
        slot_end = current + timedelta(minutes=20)
        if slot_end > end_dt:
            break  # Don't create partial slots
        
        slot = Slot(doctor_id=doctor.id, start_time=current, end_time=slot_end)
        session.add(slot)
        current = slot_end
        slots_created += 1
    
    session.commit()

    return RedirectResponse(url="/doctor-dashboard", status_code=303)

@router.post("/cancel-appointment/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    
    # Get the appointment
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #f44336;">Appointment not found</h1>
            <a href="/patient-dashboard" style="color: #667eea;">Back to Dashboard</a>
        </body>
        </html>
        """)
    
    # Verify the appointment belongs to this patient
    if appointment.patient_id != int(user_id):
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #f44336;">Unauthorized</h1>
            <p>You can only cancel your own appointments.</p>
            <a href="/patient-dashboard" style="color: #667eea;">Back to Dashboard</a>
        </body>
        </html>
        """)
    
    # Check if appointment is more than 10 hours away
    if appointment.slot:
        slot_time = appointment.slot.start_time
        if slot_time.tzinfo is None:
            slot_time = slot_time.replace(tzinfo=timezone.utc)
        
        current_time = datetime.now(timezone.utc)
        time_diff = slot_time - current_time
        hours_until = time_diff.total_seconds() / 3600
        
        if hours_until <= 10:
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cannot Cancel</title>
                <style>
                    body {{ font-family: Arial; display: flex; justify-content: center; align-items: center; 
                           height: 100vh; background: #f5f7fa; margin: 0; }}
                    .error-box {{ background: white; padding: 40px; border-radius: 15px; 
                                 box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center; max-width: 500px; }}
                    h1 {{ color: #f44336; margin-bottom: 20px; }}
                    p {{ color: #555; margin-bottom: 30px; line-height: 1.6; }}
                    a {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; 
                        border-radius: 8px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="error-box">
                    <h1>⚠️ Cannot Cancel Appointment</h1>
                    <p>Sorry, you can only cancel appointments that are more than 10 hours away.</p>
                    <p>Your appointment is in <strong>{hours_until:.1f} hours</strong>.</p>
                    <p>Please contact the doctor's office directly if you need to cancel.</p>
                    <a href="/patient-dashboard">Back to Dashboard</a>
                </div>
            </body>
            </html>
            """)
        
        # Free up the slot
        slot = appointment.slot
        slot.is_booked = False
        session.add(slot)
    
    # Delete the appointment
    session.delete(appointment)
    session.commit()
    
    # Redirect back with success message
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Appointment Cancelled</title>
        <meta http-equiv="refresh" content="2;url=/patient-dashboard">
        <style>
            body { font-family: Arial; display: flex; justify-content: center; align-items: center; 
                   height: 100vh; background: #f5f7fa; margin: 0; }
            .success-box { background: white; padding: 40px; border-radius: 15px; 
                          box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #4caf50; margin-bottom: 20px; }
            p { color: #555; }
        </style>
    </head>
    <body>
        <div class="success-box">
            <h1>✓ Appointment Cancelled Successfully</h1>
            <p>The time slot has been freed for other patients.</p>
            <p>Redirecting to dashboard...</p>
        </div>
    </body>
    </html>
    """)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie("user_role")
    return response