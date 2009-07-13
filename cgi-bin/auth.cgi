#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use lib '..';
use CGI qw/:standard/;
use Sitka::DB;

$q = new CGI;

print header,
			start_html('Authentication'),
			h1('Authenticating...');

fail('Please login.') unless (param()); # TODO: write a messaging system to handle fail() msgs

if (param()) {
	my $usr = param('usr');
	my $pwd = param('pwd');
	print p("Username: $usr");

  my $db = Sitka::DB->connect();
  my $usrdata = $db->selectrow_hashref("SELECT usrname, passwd FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    print p("Authenticated!");
  } else {
    print p("FAIL!");
  }

}

# TODO: Flag this session as authenticated, set $ou, and proceed to lookup.cgi

print p("All done!");
print end_html;

sub fail {
	my $msg = shift;
	print $q->h1('Error'),
				$q->p($msg),
				$q->end_html;
	exit;
}

