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
use Sitka::Patron;

$cgi = new CGI;

print header,
			start_html('Looking Up Patron'),
			h1('Looking Up...');

# Message codes:
# OK                 => Patron can be deleted.
# FAIL_NOT_FOUND     => Patron does not exist or does not belong to this library.
# FAIL_ACTIVE_XACTS  => Patron has active circulations or holds.
# FAIL_HAS_FINES     => Patron owes more than $0 in fines.

$ou = 0; # set this to authenticated user's OU? or more complex for multibranch?

if (param()) {
  fail('No org unit specified.') unless ($ou);
  my @input = split(/\n/, param('barcodes'));
  my (@patrons, @not_found);
  my @barcodes = clean_and_validate(@input);
  while (@barcodes) {
    my $barcode = shift @barcodes;
    my $patron = Sitka::Patron->new($barcode);
    if ($patron->retrieve()) {
      $patron->check_activity();
      $patron->check_fines();
      push @patrons, $patron;
    } else {
      push @not_found, $barcode;
    }
  }
}

print $cgi->headers,
      $cgi->start_html('Confirm Deletions'),
      $cgi->h1('Confirm Deletions');

print $cgi->h2('To Be Deleted');

if (!@patrons) {

  print $cgi->p('No patrons to delete.');

} else {

  # form to confirm deletions (action="delete.cgi") based on results of the above checks
  print $cgi->start_form( -method => 'POST', -action => 'delete.cgi' ),
        $cgi->p('Use the checkboxes to indicate which patrons you want to delete.'),
        $cgi->start_table;

  foreach my $patron (@patrons) {
    my @msgs;
    my $checked = ( $patron->msgs ? 'checked' : undef );
    if ( grep {'FAIL_ACTIVE_XACTS' eq $_} $self->msgs ) {
      push @msgs, 'Patron has ', ($patron->circs || '0'), ' active circulations and ', ($patron->holds || '0') ' active holds.';
    }
    if ( grep {'FAIL_HAS_FINES' eq $_} $self->msgs ) {
      push @msgs, 'Patron has $', $patron->fines, ' in unpaid fines.';
    }

    # output as HTML
    print $cgi->tr(
      $cgi->td($cgi->checkbox($checked)),
      $cgi->td(
        $cgi->p( join(', ', ($patron->familyname, $patron->givenname)) ),
        $cgi->div( join($cgi->br, @msgs ) )
      )
    );
  }

  print $cgi->end_table;
  print $cgi->submit('submit','Delete Checked Patrons'),
        $cgi->end_form();
}

# list barcodes not found in system
print $cgi->h2('Not Found'),
      $cgi->p('The following barcodes were not found in Evergreen:'),
      $cgi->pre( join("\n", @not_found) );

print end_html;

sub clean_and_validate {
  my @input = @_;
  my @output;
  while (@input) {
    my $barcode = shift @input;
    # TODO: clean up and validate barcodes
    push (@output, $barcode);
  }
  # TODO: remove duplicates from output
  return @output;
}

sub fail {
  my $msg = shift;
  print $msg;
  exit;
}

