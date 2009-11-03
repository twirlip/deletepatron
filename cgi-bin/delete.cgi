#!/usr/bin/perl
# delete.cgi - delete patrons from database (based on checks in confirm.cgi) and report results
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5';
use CGI qw/:standard/;
use CGI::Session qw/-ip-match/;
use HTML::Template;
use Sitka::Session;
use Sitka::Patron;
use Data::Dumper;

my $cgi = CGI->new;
my $session = Sitka::Session->new;

# check for authorization (i.e. see if user has a valid cookie)
my $sid = $cgi->cookie('CGISESSID') || undef;
$session->initialize_session($sid);
$session->login( [{error => 'NOT_LOGGED_IN'}] ) unless ($session->{cgisession}->param('_IS_LOGGED_IN'));

my $patrons = $session->{cgisession}->param('patrons');
my @not_deleted = @{$session->{cgisession}->param('cannot_delete')};
my @not_found = @{$session->{cgisession}->param('not_found')};
my @invalid = @{$session->{cgisession}->param('invalid')};
my @deleted;

# delete selected patrons from database
if ($cgi->param()) {
  foreach my $barcode ($cgi->param('delete[]')) {
    my $patron = $patrons->{$barcode};
    if ($session->type eq 'DELETE_CARD') {
      my $type = 'cards';
      my $usr_rows_updated = $patron->delete_card();
    } elsif ($session->type eq 'DELETE_PATRON') {
      my $type = 'patrons';
      my $usr_rows_updated = $patron->delete_patron();
    }
    if ($usr_rows_updated) {
      push @deleted, $patron->barcode;
    } else {
      unshift @not_deleted, $patron->barcode . ( $patron->msgs ? ' (' . $patron->msgs . ')' : '' );
    }
  }
}

# report back on what we just did
print $cgi->header,
      $cgi->start_html( -title => 'Sitka Patron Deletions - Deletion Report',
                        -style => { -src => "style.css" },
                      ),
      $cgi->h1('Deletion Report');
print $cgi->h2(ucfirst($type) . ' Deleted'), $cgi->pre( @deleted ? join("\n",@deleted) : "No $type were deleted." );
print $cgi->h2('Not Deleted'), $cgi->pre(join("\n",@not_deleted)) if (@not_deleted);
print $cgi->h2('Not Found'),   $cgi->pre(join("\n",@not_found))   if (@not_found);
print $cgi->h2('Invalid'),     $cgi->pre(join("\n",@invalid))     if (@invalid);
print $cgi->end_html;

# delete this session for security reasons
$session->{cgisession}->delete();
undef $session;
