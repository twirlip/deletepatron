#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use lib '..';
use lib '/openils/lib/perl5/';
use CGI;
use CGI::Session;
use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;
use Data::Dumper;

$cgi = new CGI;

@fail = ();
push @fail, 'MISSING_PARAMS' unless (param('usr') && param('pwd'));

my $usr = $cgi->param('usr');
my $pwd = $cgi->param('pwd');

fail() unless (authenticate($usr, $pwd));

# TODO: Flag this session as authenticated, set $ou, and proceed to input.cgi
print $cgi->header( -cookie=>$cookie );

# returns session ID if user is authenticated, else returns nothing
sub authenticate {
  my $usr = shift;
  my $pwd = shift;
  my $usr_id;
  my $home_ou;

  # TODO: do this via OpenSRF API rather than direct DB lookup
  my $db = Sitka::DB->connect();
  my $usrdata = $db->selectrow_hashref("SELECT id, usrname, passwd, home_ou FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    $usr_id  = $usrdata->{id};
    $home_ou = $usrdata->{home_ou};
  } else {
    push @fail, 'INVALID_LOGIN';
    return;
  }

  # make sure this user has permission to delete users
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $apputils = OpenILS::Application::AppUtils;
  my $p = $apputils->check_perms($usr_id, $home_ou, 'DELETE_USER');
  if ($p) {
    push @fail, 'MISSING_PERMS: ' . $p->{textcode} . ": " . $p->{desc};
    return;
  }

  # user is authenticated! create a session and cookie
  $session = new CGI::Session("driver:File", undef, {Directory=>"/tmp"});
  $cookie = $cgi->cookie(CGISESSID => $session->id);
  return $session->id;
}

# TODO: write a proper messaging system in Sitka.pm to handle fail() msgs
sub fail {
  print $cgi->header,
        $cgi->start_html('Error'),
        $cgi->h1('Error');
  foreach $failmsg (@fail) {
    print $cgi->p($failmsg);
  }
  print $cgi->end_html;
  exit;
}

