"""
Example: Create Daily Priority Plan workflow
"""

from src.main import BusinessCopilot
from datetime import datetime


def main():
    print("=" * 60)
    print("🤖 Business AI Copilot - Priority Plan Example")
    print("=" * 60)
    print()
    
    # Initialize
    print("Initializing copilot...")
    copilot = BusinessCopilot()
    print("✓ Ready!")
    print()
    
    # Example query
    query = "Create my priority plan for today"
    
    print(f"Query: {query}")
    print()
    print("Processing...")
    print()
    
    # Set user context
    user_context = {
        'user_email': 'john.doe@company.com',
        'role': 'Product Manager',
        'timezone': 'America/Los_Angeles',
        'preferences': {
            'morning_focus': True,
            'prefer_long_blocks': True
        }
    }
    
    # Process
    response = copilot.process_query(query, user_context)
    
    # Display
    print("=" * 60)
    print("PRIORITY PLAN:")
    print("=" * 60)
    print()
    print(response)
    print()


if __name__ == "__main__":
    main()

## **6. Expected Output**
# ```
# ==============================================================
# 🤖 Business AI Copilot - Priority Plan Example
# ==============================================================

# Initializing copilot...
# ✓ Ready!

# Query: Create my priority plan for today

# Processing...

# ==============================================================
# PRIORITY PLAN:
# ==============================================================

# # 🗓️ Daily Priority Plan - Tuesday, February 11, 2026

# ## 📊 Overview

# **Total Tasks:** 6
# **High Priority:** 2
# **Meetings:** 105 minutes
# **Available Time:** 435 minutes

# ## 🎯 Top Priorities

# 1. ⚠️ **Follow up on vendor API key delay** (Score: 99.0)
#    - Project: Phoenix
#    - Due: 2026-02-12
#    - ⚠️ BLOCKED: Waiting on vendor response

# 2. 🔴 **Review API spec for payment integration** (Score: 88.0)
#    - Project: Phoenix
#    - Due: 2026-02-11

# 3. 🔴 **Review Q1 roadmap with Atlas team** (Score: 78.0)
#    - Project: Atlas
#    - Due: 2026-02-14

# 4. 🟡 **Prepare sprint demo slides** (Score: 59.0)
#    - Project: Phoenix
#    - Due: 2026-02-15

# 5. 🟡 **Approve design mockups for Atlas v2** (Score: 48.0)
#    - Project: Atlas
#    - Due: 2026-02-18

# ## 📅 Your Schedule

# **09:00 AM - 09:15 AM:** 📞 Daily Standup - Phoenix Team
# **09:15 AM - 11:15 AM:** 🎯 Review API spec for payment integration (Deep Work)
# **11:15 AM - 12:00 PM:** Buffer time for email & prep
# **12:00 PM - 01:00 PM:** 🍽️ Lunch
# **01:00 PM - 02:00 PM:** 🎯 Follow up on vendor API key delay (Focused Task)
# **02:00 PM - 03:00 PM:** 📞 Design Review - Payment Flow
# **03:00 PM - 04:00 PM:** 🎯 Review Q1 roadmap with Atlas team (Focused Task)
# **04:00 PM - 04:30 PM:** 📞 1:1 with Sarah (Product Sync)
# **04:30 PM - 06:00 PM:** Wrap-up & planning

# # ## 💡 Suggestions

# # - ⚠️ CRITICAL: 1 blocked task(s) need immediate escalation
# # - 🎯 1 task(s) due today - prioritize completion
# # - ⏰ 1 high-priority task(s) not scheduled - may need to defer lower-priority work

# # ## ⚡ Quick Actions

# # - View detailed task breakdown
# # - Reschedule meetings for more focus time
# # - Mark tasks as complete
# # - Get help with blockers