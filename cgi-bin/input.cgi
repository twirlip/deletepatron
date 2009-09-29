#!/usr/bin/perl
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use CGI;
use CGI::Session qw/-ip-match/;
use Sitka::Session;

$cgi = CGI->new;

# create new session or initialize existing session
my $session = new CGI::Session(undef, $cgi, {Directory=>"/tmp"});

# authenticate user
my $authenticated_usr = Sitka::Session->authenticate($cgi->param('usr'), $cgi->param('pwd'));

if ($authenticated_usr) {

  # save user info for future use
  $session->param('usr', $authenticated_usr);

  # form for entering patron barcodes to delete
  print $cgi->header,
        $cgi->start_html('Enter Patron Barcodes'),
        $cgi->h1('Enter Patron Barcodes');
  print $cgi->start_form( -method=>'POST', -action=>'confirm.cgi');
  print $cgi->p('Please enter list of patron barcodes to be deleted, one per line.'),
        $cgi->textarea('barcodes','',10,30),
        $cgi->submit('submit','Submit');
  print $cgi->end_form();
  print $cgi->end_html();

} else {
  @msgs = ('Invalid login or user lacks DELETE_USER permission.');
  Sitka::Session->login(\@msgs);
}
