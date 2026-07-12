# UI/UX Design Guide - MedFlow AI

## 1. Design Principles
- Workflow-first design: interfaces prioritize speed and clarity for time-sensitive diagnostic operations.
- Role-centered experience: each role sees only the actions and metrics needed for immediate decisions.
- Progressive disclosure: advanced details appear contextually to reduce cognitive load.
- Trust and accountability: status changes, timestamps, and ownership are always visible.
- Accessibility by default: keyboard, contrast, and assistive support are non-negotiable.

## 2. Audience and Context
- Doctors: need rapid request creation and quick status visibility during consultation.
- Laboratory scientists and radiographers: need queue-focused interfaces with clear priorities.
- Nurses and reception: need patient movement and scheduling coordination views.
- Administrators: need analytics dashboards and exception visibility.
- Device context: desktop-first for departmental operations, responsive tablet/mobile views for ward and front-desk mobility.
- Environmental context: bright clinical lighting, intermittent connectivity, and high-interruption workflows.

## 3. Information Architecture
- Primary navigation sections:
	- Dashboard
	- Patients
	- Appointments
	- Laboratory
	- Radiology
	- Notifications
	- Analytics
	- Admin
- Role-based navigation rendering hides unauthorized modules.
- Core objects use consistent hierarchy: Patient -> Request -> Status Timeline -> Action Panel.

## 4. Design System Foundations
### 4.1 Color System
- Primary: #0A7F5A (Clinical Green)
- Secondary: #145DA0 (Diagnostic Blue)
- Accent: #F59E0B (Attention)
- Danger: #D92D20 (Critical/Error)
- Neutral scale: #0F172A to #F8FAFC

Status colors:
- Requested: Blue
- In Progress: Amber
- Completed: Green
- Cancelled/Failed: Red

### 4.2 Typography
- Primary font: Inter (UI text and data density readability).
- Secondary font: Source Sans 3 for long-form text where needed.
- Scale:
	- H1: 32/40
	- H2: 24/32
	- H3: 20/28
	- Body: 16/24
	- Caption: 14/20

### 4.3 Layout and Spacing
- 12-column responsive grid for desktop.
- 8px baseline spacing system.
- Dense table mode for high-volume queue pages.
- Sticky action bars for long clinical forms.

### 4.4 Component System
- Core components:
	- Role-aware sidebar navigation
	- Request status chips
	- Patient summary cards
	- Queue tables with inline actions
	- Timeline activity feed
	- Notification panel and toasts
	- KPI cards and trend charts

## 5. Interaction Patterns
- Forms:
	- Inline validation with concise actionable error messages.
	- Autosave for long request forms where safe.
- Data tables:
	- Sort/filter/search presets for common departmental views.
	- Bulk actions for administrative updates with confirmation modals.
- Notifications:
	- Event severity levels and acknowledgment actions.
	- Persistent bell center plus contextual in-page prompts.
- Error handling:
	- Human-readable errors with retry paths.
	- Request identifier displayed for support tracing.
- AI recommendations (future phase):
	- Display confidence, rationale summary, and clinician override controls.

## 6. Responsive Behavior
- Desktop (>= 1280px): full dashboard and multi-panel workflows.
- Tablet (768px-1279px): collapsible sidebar, stacked panels for queue and details.
- Mobile (< 768px): priority actions only, simplified queue cards, minimal chart rendering.

## 7. Accessibility Requirements
- WCAG 2.2 AA minimum compliance target.
- Full keyboard navigation with visible focus indicators.
- Minimum color contrast ratio of 4.5:1 for normal text.
- Screen reader labels for all interactive controls and status updates.
- Avoid color-only status communication; pair with icon/text labels.

## 8. Navigation and Core User Flows
### Doctor Flow
Login -> Create diagnostic request -> Set urgency -> Submit -> Track status -> Review completion.

### Laboratory Flow
Login -> Open queue -> Claim request -> Update status -> Complete/verify -> Notify requester.

### Radiology Flow
Login -> Manage scheduled requests -> Update scan status -> Attach report readiness -> Complete.

### Reception and Nursing Flow
Login -> Manage appointments/check-in -> Track patient movement -> Coordinate handoffs.

### Administrator Flow
Login -> Review live operational KPIs -> Drill down by department -> Export report.

## 9. Usability Validation Plan
- Monthly moderated role-based usability sessions.
- Clinical simulation drills for high-throughput and exception scenarios.
- Task completion targets:
	- New request creation under 60 seconds.
	- Queue status update under 15 seconds.
	- Appointment check-in workflow under 30 seconds.
- SUS and role satisfaction scores tracked per release.

## 10. Design-to-Engineering Handoff
- Required artifacts:
	- Annotated Figma screens
	- Interaction notes and edge-case behavior
	- Accessibility acceptance checklist
	- Component token references (color, spacing, typography)
- Handoff readiness gate includes product and engineering sign-off.
