close all
clear

load('val_dsc_dm.mat');
load('train_dsc_dm.mat');
load('val_dsc_bn.mat');
load('train_dsc_bn.mat');
load('val_dsc_un.mat');
load('train_dsc_un.mat');
load('val_loss_dm.mat');
load('train_loss_dm.mat');
load('val_loss_bn.mat');
load('train_loss_bn.mat');
load('val_loss_un.mat');
load('train_loss_un.mat');


colourMap = containers.Map('KeyType', 'char', 'ValueType', 'any');
colourMap('bn') = [0 0.4470 0.7410];
x = linspace(1,100);

figure(1)
plot(x, a, 'r--', x, a1, 'r', 'linewidth', 0.8); 
hold on
%plot(x, loss_bn, 'Color', colourMap('bn')); 
plot(x, loss_bn, 'b--', x, val_loss_bn, 'b', 'linewidth', 0.8);
hold on
plot(x, a4, 'k--', x, a5, 'k', 'linewidth', 0.8); 
grid on
xticks([0:20:100]);
%yticks([0:0.4:1.9]);
xlabel('Number of Epochs', 'fontsize', 11);
ylabel('Loss (BCE + DSC)', 'fontsize', 11);
legend('DeepMedic training', 'DeepMedic validation', 'Brave-Net training', 'Brave-Net validation', 'U-Net training', 'U-Net validation', 'fontsize', 11);

figure(2)
plot(x, b, 'r--', x, b1, 'r', 'linewidth', 0.8); 
hold on
plot(x, b2, 'b--', x, b3, 'b', 'linewidth', 0.8);
hold on
plot(x, b4, 'k--', x, b5, 'k', 'linewidth', 0.8); 
grid on
xticks([0:20:100]);
ylim(0:1);
yticks(0:0.1:1);
xlabel('Number of Epochs', 'fontsize', 11);
ylabel('DSC', 'fontsize', 11);
legend('DeepMedic training', 'DeepMedic validation', 'Brave-Net training', 'Brave-Net validation', 'U-Net training', 'U-Net validation', 'fontsize', 11, 'location', 'southeast');