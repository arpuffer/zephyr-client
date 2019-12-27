''' Very rough happy-path test '''

from zephyr import Zephyr

test = Zephyr()
viiihw_project = test.project('VIIIHW')
ver = viiihw_project.versions[-1]
print("Version: %s" % str(ver.__dict__))
cycles = ver.cycles
cycle = cycles[-1]
print("Cycle: %s" % str(cycle.__dict__))

folders = cycles[-1].folders
for f in folders:
    print("Folder: %s" % str(f.__dict__))

folder = folders[0]

executions = folder.executions
for e in executions:
    print("Execution: %s" % str(e.__dict__))