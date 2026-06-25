"""Create desktop shortcut for IRE-AGI"""
import pylnk3, os
desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
lnk_path = os.path.join(desktop, 'IRE-AGI.lnk')
target_vbs = os.path.join(desktop, 'IRE-AGI', '启动IRE-AGI.vbs')
work_dir = os.path.join(desktop, 'IRE-AGI')
if os.path.exists(lnk_path):
    os.remove(lnk_path)
lnk = pylnk3.for_file(
    target_file=r'C:\Windows\System32\wscript.exe',
    lnk_name=lnk_path,
    arguments='"' + target_vbs + '"',
    work_dir=work_dir,
    description='IRE-AGI v4.0'
)
print('Shortcut created at:', lnk_path)
print('Exists:', os.path.exists(lnk_path))
