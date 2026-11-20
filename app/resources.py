"""Project Noor — Verified helpline and resource directory.

Every entry here was verified against public sources (findahelpline.com,
progress.guide, official org pages) before being added. Sources and a
`verified_date` are cited per entry so reviewers can re-check and so the
UI can show "last verified" to build trust.

DO NOT add a helpline here unless you can cite a public source AND set a
verified_date. A wrong crisis number is worse than none.
"""
from __future__ import annotations

# Verified on this date (re-verify quarterly per the content review process).
VERIFIED_DATE = "2026-11-20"

# National emergency comes first — it is the one number everyone should know.
EMERGENCY = [
    {
        "name": "National Emergency (Police / Ambulance / Fire)",
        "phone": "999",
        "hours": "24/7",
        "for_whom": "Immediate danger to life, safety, or property",
        "note_bn": "যদি এখনই জীবনের ঝুঁকি থাকে — সরাসরি ৯৯৯ এ কল করুন।",
        "note_en": "If life is in danger right now — call 999 directly.",
        "source": "Government of Bangladesh national emergency number.",
        "verified_date": VERIFIED_DATE,
    },
]

# Verified mental-health and emotional-support helplines.
HELPLINES = [
    {
        "name": "Kaan Pete Roi",
        "phones": ["01779554391", "01779554392", "09612-119911"],
        "hours": "Daily, 3 PM – 3 AM (some lines 24/7)",
        "for_whom": "Anyone in despair, isolation, or having suicidal thoughts",
        "note_bn": "বাংলাদেশের প্রথম ও একমাত্র আত্মহত্যা-প্রতিরোধ হেল্পলাইন। "
                   "প্রশিক্ষিত স্বেচ্ছাসেবক, গোপনীয়, বিচারহীন শ্রবণ।",
        "note_en": "Bangladesh's first and only suicide-prevention helpline. "
                   "Trained volunteers, confidential, non-judgmental listening. "
                   "Member of Befrienders Worldwide.",
        "source": "findahelpline.com/countries/bd; kaanpeteroi.org; progress.guide",
        "verified_date": VERIFIED_DATE,
        "tags": ["crisis", "suicide", "all-ages"],
    },
    {
        "name": "Talk Hope Bangladesh",
        "phones": ["09638-881888"],
        "hours": "24/7 (phone, WhatsApp, SMS, online chat)",
        "for_whom": "Everyone — emotional distress, anxiety, depression, "
                    "stress, self-harm, suicidal thoughts",
        "note_bn": "ফ্রি, গোপনীয়, ইনক্লুসিভ মানসিক স্বাস্থ্য ও আত্মহত্যা-প্রতিরোধ "
                   "হেল্পলাইন। ২৪/৭।",
        "note_en": "Free, confidential, inclusive mental-health and "
                   "suicide-prevention helpline. 24/7.",
        "source": "findahelpline.com/countries/bd",
        "verified_date": VERIFIED_DATE,
        "tags": ["crisis", "suicide", "all-ages", "chat"],
    },
    {
        "name": "Bangladesh Child Helpline 1098",
        "phones": ["1098"],
        "hours": "24/7",
        "for_whom": "Children and young people — any mental-health worry, "
                    "crisis, or just needing someone to talk to",
        "note_bn": "শিশু ও তরুণদের জন্য ফ্রি ও গোপনীয়। সংকটে হোক বা শুধু কথা "
                   "বলতে ইচ্ছে — কল করতে পারেন।",
        "note_en": "Free and confidential for children and youth. Whether in "
                   "crisis or just wanting to talk, you can call.",
        "source": "findahelpline.com/countries/bd; progress.guide",
        "verified_date": VERIFIED_DATE,
        "tags": ["crisis", "youth", "children"],
    },
    {
        "name": "Vent by Mindspace",
        "phones": ["09678-678778"],
        "hours": "See official page for current hours",
        "for_whom": "Adults and youth ~15–30 — anxiety, depression, loneliness, "
                    "family or relationship conflict, addiction",
        "note_bn": "নির্দিষ্ট বয়সের জন্য — উদ্বেগ, হতাশা, একাকীত্ব, পরিবার "
                   "বা সম্পর্কের সমস্যা। প্রশিক্ষিত স্বেচ্ছাসেবক।",
        "note_en": "For a specific age range — anxiety, depression, loneliness, "
                   "family or relationship issues. Trained volunteers supervised "
                   "by qualified professionals.",
        "source": "findahelpline.com/countries/bd",
        "verified_date": VERIFIED_DATE,
        "tags": ["youth", "anxiety", "depression"],
    },
    {
        "name": "Helpline for Victims of Violence (BMP)",
        "phones": ["01717-363647"],
        "hours": "See official page for current hours",
        "for_whom": "Women and girls facing physical, emotional, sexual, or "
                    "economic violence",
        "note_bn": "নারী ও মেয়েদের জন্য — সহায়তা, কাউন্সেলিং, আইনি পরামর্শ, "
                   "রেফারেল। ফ্রি ও গোপনীয়।",
        "note_en": "For women and girls — support, counselling, legal advice, "
                   "referrals. Free and confidential.",
        "source": "findahelpline.com/countries/bd",
        "verified_date": VERIFIED_DATE,
        "tags": ["women", "violence", "safety"],
    },
    {
        "name": "Alapon Helpline",
        "phones": ["09678-609609"],
        "hours": "See official page for current hours",
        "for_whom": "Youth wanting someone to talk to",
        "note_bn": "তরুণদের জন্য একটি কথা বলার হেল্পলাইন।",
        "note_en": "A listening helpline for youth.",
        "source": "findahelpline.com/countries/bd",
        "verified_date": VERIFIED_DATE,
        "tags": ["youth"],
    },
]

# Non-emergency, longer-term options (clinics, directories). Marked as
# "verify before visiting" because clinic details change.
LONG_TERM = [
    {
        "name": "National Institute of Mental Health (NIMH)",
        "location": "Sher-e-Bangla Nagar, Dhaka",
        "note_bn": "সরকারি মানসিক স্বাস্থ্য হাসপাতাল ও গবেষণা প্রতিষ্ঠান। "
                   "ভিজিটের আগে অফিসিয়াল নম্বর যাচাই করে নিন।",
        "note_en": "Government mental-health hospital and research institute. "
                   "Verify the current appointment number on the official "
                   "website before visiting.",
        "source": "Government of Bangladesh; verify current contact on official site.",
        "verified_date": VERIFIED_DATE,
        "tags": ["clinic", "government"],
    },
]


def get_all():
    return {"emergency": EMERGENCY, "helplines": HELPLINES,
            "long_term": LONG_TERM, "verified_date": VERIFIED_DATE}


def get_for_crisis():
    """Short list shown inside the chat UI when a crisis signal fires."""
    out = list(EMERGENCY)
    for h in HELPLINES:
        if "crisis" in h.get("tags", []) or "suicide" in h.get("tags", []):
            out.append(h)
    return out
