#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use Sitka::Session;

Sitka::Session->login;
