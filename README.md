# DEFCON 2020 Quals Ooonline GradClass

This challenge is an online course system modeled after coursera's custom grader. It is the fixed version of ooonline-class.

## Vulnerabilities

- SQL injection for users to extract the admin creds (so that they can get access to the container environment)

- Admin creds give access to the grading binary. This shows you how
your C file is compiled and executed.


## Exploit

[The exploit](./interaction/exploit.py) use the `/proc` filesystem to
overwrite your parent's output. This must be done in a tight loop
because your parent will always write out the status, so you must race
and succeed.
