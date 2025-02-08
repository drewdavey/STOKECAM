% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-12-16


clear; clc; close all;

%% Load data

vn = readtable('FA_3E_0073_0331_0279_0006_0207.csv');

rp = readtable('latency_test2.txt');

%% Parse data

% Raw time
t_rp = rp.Var1;
t_rp_vn = vn.systemTimeStamp;
t_vn = vn.timeStartup;

% % Relative time
% t_rp = rp.Var1 - rp.Var1(1);
% t_rp_vn = vn.systemTimeStamp - vn.systemTimeStamp(1);
% t_vn = vn.timeStartup - vn.timeStartup(1);
% 
% % Relative time in sec
% t_rp = t_rp *1e-9;
% t_rp_vn = t_rp_vn *1e-9;
% t_vn = t_vn *1e-9;

idx = 1:length(t_vn);

figure; grid on; box on; hold on;
plot(idx,t_rp_vn,'--r','LineWidth',2);
plot(idx,t_vn,'-b','LineWidth',1);
xlabel('idx');
ylabel('time (ns)');
% ylabel('relative time (sec)');
title('systemTimeStamp vs. timeStartup');

% Compute slopes
slope_rp_vn = (t_rp_vn(end) - t_rp_vn(1)) / length(idx);
slope_vn = (t_vn(end) - t_vn(1)) / length(idx);

figure; grid on; box on; hold on;
plot(idx,t_rp,'--r','LineWidth',2);
plot(idx,t_rp_vn,'-b','LineWidth',1);
xlabel('idx');
ylabel('time (ns)');
% ylabel('relative time (sec)');
title('systemTimeStamp vs. RP monotonic time');

% Difference bw sysTS and timeSt
dt1 = t_rp_vn(2:end) - t_vn(2:end);
dt1 = dt1 - mean(dt1); % take out mean
dt1 = dt1 * 1e-6; % put into milliseconds

figure; grid on; box on; hold on;
plot(idx(2:end),dt1,'-b','LineWidth',1);
xlabel('idx');
ylabel('difference (ms)');
% ylabel('relative time (sec)');
title('(systemTimeStamp - timeStartup)');

variance_packet = var(dt1); % variance
std_packet = std(dt1); % std
