#!/usr/bin/perl
# delete.cgi - delete patrons from database (based on checks in confirm.cgi) and report results
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5';
use OpenSRF::Utils::Logger;
use CGI qw/:standard/;
use CGI::Session qw/-ip-match/;
use HTML::Template;
use Sitka::Session;
use Sitka::Patron;
use Data::Dumper;

my $cgi = CGI->new;
my $session = Sitka::Session->new;

my $logger = OpenSRF::Utils::Logger;

# check for authorization (i.e. see if user has a valid cookie)
my $ckey = $cgi->param('ckey') || undef; # TODO: this assumes we're still using a cookie to store the session id, despite our use of memcached
$session->retrieve_session($ckey);
$session->login() unless $session->{authtoken};

my $patrons = $session->{patrons};
my $not_deleted = $session->{cannot_delete};
my $usr_is_active = $session->{usr_is_active};
my $not_found = $session->{not_found};
my $invalid = $session->{invalid};
my @deleted;
my @unchecked;

print $cgi->header,
      $cgi->start_html( -title => 'Sitka Patron Deletions - Deletion Report',
                        -style => { -src => "style.css" },
                      ),
      $cgi->h1('Deletion Report');

my $type;
if ($session->type eq 'DELETE_CARD') {
  $type = 'cards';
} elsif ($session->type eq 'DELETE_PATRON') {
  $type = 'patrons';
}

# delete selected patrons from database
if ($cgi->param()) {
  foreach my $barcode ($cgi->param('delete[]')) {
    my $result;
    my $patron = $patrons->{$barcode};
    if ($session->type eq 'DELETE_CARD') {
      $result = $patron->delete_card($session->{authtoken});
    } elsif ($session->type eq 'DELETE_PATRON') {
      $result = $patron->delete_patron($session->{authtoken});
    }
    if ($result) {
      push @deleted, $patron->barcode;
    } else {
      unshift @not_deleted, $patron->barcode . ( $patron->msgs ? ' (' . $patron->msgs . ')' : '' );
    }
  }
}

$logger->info("DELETEPATRON: $type deleted: " . join(' ', @deleted));

# report back on what we just did
print $cgi->h2(ucfirst($type) . ' Deleted'), $cgi->pre( @deleted ? join("\n",@deleted) : "No $type were deleted." );
if ( @$not_deleted || @$usr_is_active ) {
  print $cgi->h2('Not Deleted');
  print $cgi->pre(join("\n",@$not_deleted)) if (@$not_deleted);
  print $cgi->pre(join("\n",@$usr_is_active)) if (@$usr_is_active);
}
print $cgi->h2('Not Found'),   $cgi->pre(join("\n",@$not_found))   if (@$not_found);
print $cgi->h2('Invalid'),     $cgi->pre(join("\n",@$invalid))     if (@$invalid);
print $cgi->end_html;

