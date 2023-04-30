from flask import render_template


# route
def shifts():
  return render_template('shifts.html')

def all_shifts():
  return render_template('all_shifts.html')