#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use CGI;
use Sitka::DB;

fail('Please login.') unless (param()); # TODO: write a messaging system to handle fail() msgs

my $usr = param('usr');
my $pwd = param('pwd');

my $db = Sitka::DB->new;
my @usr = $db->lookup('SELECT usr, profile, home_ou FROM actor.usr WHERE usrname = ? AND passwd = md5(?);', $usr, $pwd);

fail('Username or password incorrect.') unless (@usr);

# TODO: Flag this session as authenticated, set $ou, and proceed to lookup.cgi

