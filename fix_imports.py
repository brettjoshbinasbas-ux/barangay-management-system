import sys 
with open('Panels/login.py', 'r') as f: 
    content = f.read() 
 
content = content.replace('from staff_dashboard', 'from Panels.staff_dashboard') 
content = content.replace('from admin_dashboard', 'from Panels.admin_dashboard') 
 
with open('Panels/login.py', 'w') as f: 
    f.write(content) 
 
print('Fixed imports in login.py') 
