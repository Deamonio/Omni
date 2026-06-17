# Shared Image Rules

Use this folder for image assets that should be reused by multiple student apps.

## Folder standard

- common/: shared brand/common assets (logo, icon, background)
- students/<student_id>/: student-specific assets that are still managed in shared

## Naming convention

- Use lowercase and kebab-case only
- Recommended extensions: .svg for icons/logo, .png/.jpg for photos
- Include semantic names like login-banner, omni-logo, profile-avatar

## Flask path usage

In student app templates, use:

- {{ url_for('shared_static', filename='images/common/omni-logo.svg') }}
- {{ url_for('shared_static', filename='images/students/0000000/profile-avatar.svg') }}
