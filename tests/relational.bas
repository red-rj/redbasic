let T = 1
let F = 0

if T && T then print "if and" else print "error"
if T && F then print "error" else print "else and"
if F || T then print "if or" else print "error"
if F || F then print "error" else print "else or"
