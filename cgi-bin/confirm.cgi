#!/usr/bin/perl
# confirm.cgi - retrieve patron info, check for activity, and confirm that we want to delete 'em
#
# TODO:
#   - generate HTML output
#   - construct webform so user can confirm patron deletions
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

# TODO: check for authorization (i.e. see if user has a valid cookie)
# NB: we need to ensure that this cookie is valid specifically for patron deletions
# (can't just accept any cookie on the given domain)
my $sid = $cgi->cookie('CGISESSID') || undef;
$session->initialize_session($sid);
$session->login( [{error => 'NOT_LOGGED_IN'}] ) unless ($session->{cgisession}->param('_IS_LOGGED_IN'));

# Message codes:
# OK                 => Patron can be deleted.
# FAIL_NOT_FOUND     => Patron does not exist or does not belong to this library.
# FAIL_ACTIVE_XACTS  => Patron has active circulations or holds.
# FAIL_HAS_FINES     => Patron owes more than $0 in fines.

my $ou = $session->{cgisession}->param('ou') || 0; # set this to authenticated user's OU? or more complex for multibranch?

my @patrons; 
my @not_found;

if (param()) {
  die('No org unit specified.') unless ($ou);
  my @barcodes = clean_and_validate($cgi->param('barcodes'));
  while (@barcodes) {
    my $barcode = shift @barcodes;
    my $patron = Sitka::Patron->new($barcode, $ou);
    if ($patron->retrieve()) {
      $patron->check_activity();
      $patron->check_fines();
      push @patrons, $patron;
    } else {
      push @not_found, $barcode;
    }
  }
}

print $cgi->header,
      $cgi->start_html('Confirm Deletions'),
      $cgi->h1('Confirm Deletions');

print $cgi->h2('To Be Deleted');

if (!@patrons) {

  print $cgi->p('No patrons to delete.');

} else {

  # form to confirm deletions (action="delete.cgi") based on results of the above checks
  print $cgi->start_form( -method => 'POST', -action => 'delete.cgi' );

  my $rows; # array reference for patron data to be used by HTML::Template
  foreach my $patron (@patrons) {
    my @msgs;
    my $checkbox = 'checked';
    if ( grep {'FAIL_ACTIVE_XACTS' eq $_} $patron->msgs ) {
      push @msgs, 'Patron has ', ($patron->circs || '0'), ' active circulations and ', ($patron->holds || '0'), ' active holds.';
      $checkbox = 'disabled';
    }
    if ( grep {'FAIL_HAS_FINES' eq $_} $patron->msgs ) {
      push @msgs, 'Patron has $', $patron->fines, ' in unpaid fines.';
      undef $checkbox unless ($checkbox == 'disabled');
    }

    # TODO: eliminate HTML gobbledygook below
    push @{$rows}, {
      checkbox   => ($checkbox ? "$checkbox=\"$checkbox\"" : undef),
      barcode    => $patron->barcode,
      patronname => join(', ', ($patron->familyname, $patron->givenname)),
      msgs       => $cgi->div(join('<br />', @msgs)),
    };

  }

  # print patron info with the magic of HTML::Template
  my $template = HTML::Template->new(filename => 'rows-confirm.tmpl');
  $template->param(ROWS => $rows);
  print $template->output();

  print $cgi->submit('submit','Delete Checked Patrons'),
        $cgi->end_form();
}

# list barcodes not found in system
print $cgi->h2('Not Found'),
      $cgi->p('The following barcodes were not found in Evergreen:'),
      $cgi->pre( join("\n", @not_found) );

print end_html;

sub clean_and_validate {
  my $input = shift;
  my @barcodes = split(/[\r\n]+/, $input);
  my @clean_barcodes;
  foreach my $barcode (@barcodes) {
    next if ($barcode =~ /^\s*$/); # discard blank lines
    # TODO: clean up and validate barcodes
    push (@clean_barcodes, $barcode);
  }
  # remove duplicate barcodes
  my %hash = map {$_ => 1} @clean_barcodes;
  my @unique_barcodes = keys %hash;
  return @unique_barcodes;
}

