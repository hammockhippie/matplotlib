from matplotlib.matlab import *

def f(t):
    s1 = cos(2*pi*t)
    e1 = exp(-t)
    return multiply(s1,e1)

t1 = arange(0.0, 5.0, .1)
t2 = arange(0.0, 5.0, 0.02)
t3 = arange(0.0, 2.0, 0.01)

figure(1, size=(800,600))
subplot(211)
l = plot(t1, f(t1), 'k^')
set(l, 'markerfacecolor', 'k')
set(l, 'markeredgecolor', 'r')
#set(l, 'linewidth', 3)
#set(l, 'markersize', 12)
title('A tale of 2 subplots', fontsize=14, fontname='Courier')
ylabel('Signal 1', fontsize=12)
subplot(212)
l = plot(t1, f(t1), 'k>')


ylabel('Signal 2', fontsize=12)
xlabel('time (s)', fontsize=12)

show()

