#!/usr/bin/perl
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use CGI;
use CGI::Session qw/-ip-match/;
use Sitka::Session;
use Data::Dumper;

my $cgi = CGI->new;
my $usr = $cgi->param('usr');
my $pwd = $cgi->param('pwd');

my $session = Sitka::Session->new;
$session->authenticate($usr, $pwd);

if (!$session->{authenticated}) {

  push my @msgs, { error => 'OU_NOT_FOUND' };
  Sitka::Session->login(\@msgs);

} else {

  # form for entering patron barcodes to delete
  print $session->{cgisession}->header(); # create cookie for session
  print $cgi->start_html( -title => 'Sitka Patron Deletions - Enter Patron Barcodes',
                          -style => { -src => "style.css" },
                        ),
        $cgi->h1('Enter Patron Barcodes');
  print $cgi->start_form( -method=>'POST', -action=>'confirm.cgi');
  print $cgi->p('Please enter list of patron barcodes to be deleted, one per line.'),
        $cgi->textarea('barcodes','',10,30);
  print $cgi->checkbox( -name=>'delete_cards_only', -value=>'delete_cards_only', -selected=>0, -label=>"Delete cards only" );
  print $cgi->submit('submit','Submit');
  print $cgi->end_form();
  print $cgi->end_html();

}
