#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use lib '..';
use CGI qw/:standard/;
use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;

$q = new CGI;

print header,
			start_html('Authentication'),
			h1('Authenticating...');

fail('Please login.') unless (param()); # TODO: write a messaging system to handle fail() msgs

if (param()) {
	my $usr = param('usr');
	my $pwd = param('pwd');
	print p("Username: $usr");

  # TODO: do this via OpenSRF API rather than direct DB lookup
  my $db = Sitka::DB->connect();
  my $usrdata = $db->selectrow_hashref("SELECT usrname, passwd, ud, home_ou FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    print p("Authenticated!");
  } else {
    print p("FAIL!");
  }

  # make sure this user has permission to delete users
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $apputils = OpenILS::Application::AppUtils;
  my $usr_id  = $usrdata->{id};
  my $home_ou = $usrdata->{home_ou};
  if ($apputils->check_perms($usr_id, $home_ou, 'DELETE_USER')) {
    print p("Sorry, this user doesn't seem to have that permission.\n");
  } else {
    print p("Yep, you can delete users.\n");
  }

}

# TODO: Flag this session as authenticated, set $ou, and proceed to input.cgi

print p("All done!");
print end_html;

sub fail {
	my $msg = shift;
	print $q->h1('Error'),
				$q->p($msg),
				$q->end_html;
	exit;
}

