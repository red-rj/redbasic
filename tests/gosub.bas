goto 1

L: 
print "label"
return

999  print "lineno"
1000 return

1 print "start"
gosub L
gosub 999
print "end"
