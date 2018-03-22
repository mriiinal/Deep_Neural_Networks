from __future__ import print_function
import torch
import torch.optim as optim
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F

import torchvision
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from torchvision.utils import save_image
from torch.utils.data import DataLoader

import matplotlib.pyplot as plt

from model import *

def sample_noise(batch_size, channels):
    return torch.randn(batch_size, channels, 1, 1).float()

max_iter = 25

download = False

trans = transforms.Compose([transforms.ToTensor(),
                            transforms.Normalize([0.5,], [0.5,])])

mnist = datasets.MNIST('./', train=True, transform=trans, download=True)

batch_size = 64

use_cuda = False

if __name__ == '__main__':
    d_convs = [(32, 4, 2, 1), (64, 4, 2, 1), (1, 7, 1, 0)]
    discriminator = Discriminator(d_convs)
    g_convs = [(64, 7, 1, 0), (32, 4, 2, 1), (1, 4, 2, 1)]
    generator = DCGenerator(g_convs)
    print(discriminator)
    print(generator)

    if use_cuda:
        discriminator, generator = discriminator.cuda(), generator.cuda()

    dataloader = DataLoader(mnist, batch_size=batch_size, shuffle=True)

    optimizer_d = optim.Adam(discriminator.parameters(), lr=0.0002, betas=(0.5, 0.999))
    optimizer_g = optim.Adam(generator.parameters(), lr=0.0002, betas=(0.5, 0.999))


    real_label, fake_label = 1, 0

    criterion = nn.BCELoss()

    if use_cuda:
        criterion = criterion.cuda()

    fixed_noise = sample_noise(batch_size, 1)
    if use_cuda:
        fixed_noise = fixed_noise.cuda()
    fixed_noise = Variable(fixed_noise, volatile=True)

    for epoch in range(1, max_iter+1):
        for i, (x, _) in enumerate(dataloader):
            batch_size = x.size(0)
            # training D on real data
            optimizer_d.zero_grad()
            x = Variable(x)
            if use_cuda:
                x = x.cuda()
            output = discriminator(x)
            real_v = Variable(torch.Tensor(batch_size).fill_(real_label).float())
            if use_cuda:
                real_v = real_v.cuda()
            loss_d = criterion(output, real_v)
            loss_d.backward()
            Dx = output.data.mean(dim=0)[0]
            # training D on fake data
            z = sample_noise(batch_size, 1)
            z = Variable(z)
            if use_cuda:
                z = z.cuda()

            fake = generator(z)
            output = discriminator(fake.detach())
            fake_v = Variable(torch.Tensor(batch_size).fill_(fake_label).float())
            if use_cuda:
                fake_v = fake_v.cuda()
            loss_g = criterion(output, fake_v)
            loss_g.backward()
            optimizer_d.step()

            err_D = loss_d.data[0] + loss_g.data[0]

            # training G
            optimizer_g.zero_grad()
            output = discriminator(fake)
            real_v = Variable(torch.Tensor(batch_size).fill_(real_label).float())
            if use_cuda:
                real_v = real_v.cuda()

            loss = criterion(output, real_v)
            loss.backward()
            optimizer_g.step()
            err_G = loss.data[0]
            DGz = output.data.mean(dim=0)[0]

            print('[{:02d}/{:02d}],[{:03d}/{:03d}], errD: {:.4f}, D(x): {:.4f}, errG: {:.4f}, D(G(z)): {:.4f}'.format(
                  epoch, max_iter, i, len(dataloader), err_D, Dx, err_G, DGz))

        fake = generator(fixed_noise)
        
        save_image(fake.data, './mnist-fake-{:02d}.png'.format(epoch),
                   normalize=True)