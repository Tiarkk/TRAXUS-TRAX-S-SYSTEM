# TRAXUS TRAX-S SYSTEM 

A Discord bot designed to streamline onboarding for your server, with clean slash commands, dropdowns, and a review workflow for approvals. 
The code is very far from perfect or even good. So please be gentle. However i am always eager to learn :)
---

## What It Does

- Users run `/traxus` to start the onboarding
- They pick a department, then a job from dropdown menus
- Once submitted, an application is posted to a review channel
- Approvers can approve or reject the request via buttons
- If approved:
  - The applicant gets a DM
  - Their nickname is updated to:  
    `Display Name | TRAXUS Job Title`  
    (If it’s too long, it falls back to just `TRAXUS Job Title`)
- Every step (request, approval, rejection) gets logged to a dedicated log channel


## Current Objectives
- Renaming the User doesnt work yet....
  - If Name is to long after renaming shorten Name like
      Exfiltration -> Exfil or Exf, 
      Manager -> Mgr, 
      Hygiene -> Hgn
      - If still to long just use `TRAXUS Job Title`
- notify designated head/lead when someone applies in their divison or department
- only give designated heads/leads ability to confirm/accept people in their dpt/division
- PostgreSQL support
- Weboverlay to manage executives
- docker 

## Contact
Dc Username: tiark
- Feel free to ask
