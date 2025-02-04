% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-12-16


clear; clc; close all;

%% Load data

vn = readtable('FA_3E_0073_0331_0279_0006_0207.csv');

rp = readtable('latency_test2.txt');

%% Parse data

t_rp = rp.Var1;
t_rp_vn = vn.systemTimeStamp;
t_vn = vn.timeStartup;

% % Relative time
% t_rp = rp.Var1 - rp.Var1(1);
% t_rp_vn = vn.systemTimeStamp - vn.systemTimeStamp(1);
% t_vn = vn.timeStartup - vn.timeStartup(1);

idx = 1:length(t_vn);

figure; grid on; box on; hold on;
plot(idx,t_rp_vn,'--r','LineWidth',2);
plot(idx,t_vn,'-b','LineWidth',1);
xlabel('idx');
ylabel('relative time (ns)');
title('systemTimeStamp vs. timeStartup');

figure; grid on; box on; hold on;
plot(idx,t_rp,'--r','LineWidth',2);
plot(idx,t_vn,'-b','LineWidth',1);
xlabel('idx');
ylabel('relative time (ns)');
title('systemTimeStamp vs. RP monotonic time');